#!/usr/bin/env python3
import os
import argparse
import openai
import pinecone
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Table config
PINECONE_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert PINECONE_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

# Function to query records from the Pinecone index
def query_records(index, query, top_k=1000):
    results = index.query(query, top_k=top_k, include_metadata=True)
    return [f"{task.metadata['task']}:\n{task.metadata['result']}\n------------------" for task in results.matches]

# Get embedding for the text
def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Query Pinecone index using a string.")
    parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
    main objective description. Doesn\'t need to be quoted.
    if not specified, get objective from environment.
    ''', default=[os.getenv("OBJECTIVE", "")])
    args = parser.parse_args()

    # Initialize Pinecone
    pinecone.init(api_key=PINECONE_API_KEY)

    # Connect to the objective index
    index = pinecone.Index(PINECONE_TABLE_NAME)

    # Query records from the index
    query = get_ada_embedding(' '.join(args.objective).strip())
    retrieved_tasks = query_records(index, query)
    for r in retrieved_tasks:
        print(r)

if __name__ == "__main__":
    main()
