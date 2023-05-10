import os
import csv 
import shutil
import openai
import pandas as pd
import numpy as np
from transformers import GPT2TokenizerFast
from dotenv import load_dotenv
import time

# Heavily derived from OpenAi's cookbook example

load_dotenv()

# the dir is the ./playground directory
REPOSITORY_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)), "playground")

class Embeddings:
    def __init__(self, workspace_path: str):
        self.workspace_path = workspace_path
        openai.api_key = os.getenv("OPENAI_API_KEY", "")

        self.DOC_EMBEDDINGS_MODEL = f"text-embedding-ada-002"
        self.QUERY_EMBEDDINGS_MODEL = f"text-embedding-ada-002"

        self.SEPARATOR = "\n* "

        self.tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")
        self.separator_len = len(self.tokenizer.tokenize(self.SEPARATOR))

    def compute_repository_embeddings(self):
        try:
            playground_data_path = os.path.join(self.workspace_path, 'playground_data')

            # Delete the contents of the playground_data directory but not the directory itself
            # This is to ensure that we don't have any old data lying around
            for filename in os.listdir(playground_data_path):
                file_path = os.path.join(playground_data_path, filename)

                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {str(e)}")
        except Exception as e:
            print(f"Error: {str(e)}")

        # extract and save info to csv
        info = self.extract_info(REPOSITORY_PATH)
        self.save_info_to_csv(info)

        df = pd.read_csv(os.path.join(self.workspace_path, 'playground_data\\repository_info.csv'))
        df = df.set_index(["filePath", "lineCoverage"])
        self.df = df
        context_embeddings = self.compute_doc_embeddings(df)
        self.save_doc_embeddings_to_csv(context_embeddings, df, os.path.join(self.workspace_path, 'playground_data\\doc_embeddings.csv'))

        try:
            self.document_embeddings = self.load_embeddings(os.path.join(self.workspace_path, 'playground_data\\doc_embeddings.csv'))
        except:
            pass

    # Extract information from files in the repository in chunks
    # Return a list of [filePath, lineCoverage, chunkContent]
    def extract_info(self, REPOSITORY_PATH):
        # Initialize an empty list to store the information
        info = []
        
        LINES_PER_CHUNK = 60

        # Iterate through the files in the repository
        for root, dirs, files in os.walk(REPOSITORY_PATH):
            for file in files:
                file_path = os.path.join(root, file)

                # Read the contents of the file
                with open(file_path, "r", encoding="utf-8") as f:
                    try:
                        contents = f.read()
                    except:
                        continue
                
                # Split the contents into lines
                lines = contents.split("\n")
                # Ignore empty lines
                lines = [line for line in lines if line.strip()]
                # Split the lines into chunks of LINES_PER_CHUNK lines
                chunks = [
                        lines[i:i+LINES_PER_CHUNK]
                        for i in range(0, len(lines), LINES_PER_CHUNK)
                    ]
                # Iterate through the chunks
                for i, chunk in enumerate(chunks):
                    # Join the lines in the chunk back into a single string
                    chunk = "\n".join(chunk)
                    # Get the first and last line numbers
                    first_line = i * LINES_PER_CHUNK + 1
                    last_line = first_line + len(chunk.split("\n")) - 1
                    line_coverage = (first_line, last_line)
                    # Add the file path, line coverage, and content to the list
                    info.append((os.path.join(root, file), line_coverage, chunk))
            
        # Return the list of information
        return info

    def save_info_to_csv(self, info):
        # Open a CSV file for writing
        os.makedirs(os.path.join(self.workspace_path, "playground_data"), exist_ok=True)
        with open(os.path.join(self.workspace_path, 'playground_data\\repository_info.csv'), "w", newline="") as csvfile:
            # Create a CSV writer
            writer = csv.writer(csvfile)
            # Write the header row
            writer.writerow(["filePath", "lineCoverage", "content"])
            # Iterate through the info
            for file_path, line_coverage, content in info:
                # Write a row for each chunk of data
                writer.writerow([file_path, line_coverage, content])

    def get_relevant_code_chunks(self, task_description: str, task_context: str):
        query = task_description + "\n" + task_context
        most_relevant_document_sections = self.order_document_sections_by_query_similarity(query, self.document_embeddings)
        selected_chunks = []
        for _, section_index in most_relevant_document_sections:
            try:
                document_section = self.df.loc[section_index]
                selected_chunks.append(self.SEPARATOR + document_section['content'].replace("\n", " "))
                if len(selected_chunks) >= 2:
                    break
            except:
                pass

        return selected_chunks

    def get_embedding(self, text: str, model: str) -> list[float]:
        result = openai.Embedding.create(
        model=model,
        input=text
        )
        return result["data"][0]["embedding"]

    def get_doc_embedding(self, text: str) -> list[float]:
        return self.get_embedding(text, self.DOC_EMBEDDINGS_MODEL)

    def get_query_embedding(self, text: str) -> list[float]:
        return self.get_embedding(text, self.QUERY_EMBEDDINGS_MODEL)

    def compute_doc_embeddings(self, df: pd.DataFrame) -> dict[tuple[str, str], list[float]]:
        """
        Create an embedding for each row in the dataframe using the OpenAI Embeddings API.

        Return a dictionary that maps between each embedding vector and the index of the row that it corresponds to.
        """
        embeddings = {}
        for idx, r in df.iterrows():
            # Wait one second before making the next call to the OpenAI Embeddings API
            # print("Waiting one second before embedding next row\n")
            time.sleep(1)
            embeddings[idx] = self.get_doc_embedding(r.content.replace("\n", " "))
        return embeddings

    def save_doc_embeddings_to_csv(self, doc_embeddings: dict, df: pd.DataFrame, csv_filepath: str):
        # Get the dimensionality of the embedding vectors from the first element in the doc_embeddings dictionary
        if len(doc_embeddings) == 0:
            return

        EMBEDDING_DIM = len(list(doc_embeddings.values())[0])

        # Create a new dataframe with the filePath, lineCoverage, and embedding vector columns
        embeddings_df = pd.DataFrame(columns=["filePath", "lineCoverage"] + [f"{i}" for i in range(EMBEDDING_DIM)])

        # Iterate over the rows in the original dataframe
        for idx, _ in df.iterrows():
            # Get the embedding vector for the current row
            embedding = doc_embeddings[idx]
            # Create a new row in the embeddings dataframe with the filePath, lineCoverage, and embedding vector values
            row = [idx[0], idx[1]] + embedding
            embeddings_df.loc[len(embeddings_df)] = row

        # Save the embeddings dataframe to a CSV file
        embeddings_df.to_csv(csv_filepath, index=False)

    def vector_similarity(self, x: list[float], y: list[float]) -> float:
        return np.dot(np.array(x), np.array(y))

    def order_document_sections_by_query_similarity(self, query: str, contexts: dict[(str, str), np.array]) -> list[(float, (str, str))]:
        """
        Find the query embedding for the supplied query, and compare it against all of the pre-calculated document embeddings
        to find the most relevant sections. 
        
        Return the list of document sections, sorted by relevance in descending order.
        """
        query_embedding = self.get_query_embedding(query)
        
        document_similarities = sorted([
            (self.vector_similarity(query_embedding, doc_embedding), doc_index) for doc_index, doc_embedding in contexts.items()
        ], reverse=True)
        
        return document_similarities
    
    def load_embeddings(self, fname: str) -> dict[tuple[str, str], list[float]]:       
        df = pd.read_csv(fname, header=0)
        max_dim = max([int(c) for c in df.columns if c != "filePath" and c != "lineCoverage"])
        return {
            (r.filePath, r.lineCoverage): [r[str(i)] for i in range(max_dim + 1)] for _, r in df.iterrows()
        }