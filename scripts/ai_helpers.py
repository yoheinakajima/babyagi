import openai
from dotenv import load_dotenv
from typing import Dict, List, Tuple
import os
import pinecone

class OpenAIHelper:
    def __init__(self):
        load_dotenv()
        self.configure_openai()

    def configure_openai(self) -> None:
        """Configure the OpenAI API by setting the API key."""
        openai.api_key = os.environ.get("OPENAI_API_KEY")

    @staticmethod
    def create_prompt(template: str, **kwargs) -> str:
        """
        Create a prompt string by inserting given values into a template string.

        :param template: Template string with placeholders for values.
        :param kwargs: Dictionary of values to be inserted into the template.
        :return: Formatted string with values inserted into the template.
        """
        return template.format(**kwargs)

    @staticmethod
    def process_response(response, delimiter: str = '\n') -> List[str]:
        """
        Process the response from the OpenAI API and extract the output.

        :param response: OpenAI API response.
        :param delimiter: Delimiter used to split the response text.
        :return: List of strings extracted from the response text.
        """
        return response.choices[0].text.strip().split(delimiter)

    def get_embedding(self, text: str, model: str = "text-embedding-ada-002") -> List[float]:
        """
        Get the embedding of the given text using the specified model.

        :param text: The input text to generate the embedding for.
        :param model: The OpenAI model to be used for generating the embedding.
        :return: List of float values representing the embedding.
        """
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model=model)["data"][0]["embedding"]


class PineconeHelper:
    def __init__(self):
        load_dotenv()
        self.configure_pinecone()
        self.table_name = os.environ.get("YOUR_TABLE_NAME")

    def configure_pinecone(self) -> None:
        """Configure Pinecone by setting the API key and environment key."""
        pinecone_api_key = os.environ.get("PINECONE_API_KEY")
        pinecone_env_key = os.environ.get("PINECONE_ENV_KEY")
        pinecone.init(api_key=pinecone_api_key, environment=pinecone_env_key)

    def create_index(self, dimension: int = 1536, metric: str = "cosine", pod_type: str = "s1.x1") -> None:
        """
        Create a Pinecone index with the specified parameters.

        :param dimension: Dimension of the index.
        :param metric: Metric used for similarity search.
        :param pod_type: Type of pod to be used.
        """
        if self.table_name not in pinecone.list_indexes():
            pinecone.create_index(self.table_name, dimension=dimension, metric=metric, pod_type=pod_type)

    def query_index(self, query_embedding: List[float], top_k: int = 5, include_metadata: bool = True) -> List[Tuple[str, Dict]]:
        """
        Query the Pinecone index with the given query embedding.

        :param query_embedding: Query embedding to be used for similarity search.
        :param top_k: Number of top results to be returned.
        :param include_metadata: Whether to include metadata in the results.
        :return: List of tuples containing the result ID and metadata.
        """
        index = pinecone.Index(index_name=self.table_name)
        results = index.query(query_embedding, top_k=top_k, include_metadata=include_metadata)
        sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
        return [(str(item.metadata['task']), item.metadata) for item in sorted_results]

    def upsert(self, item_id: str, item_embedding: List[float], metadata: Dict) -> None:
        """
        Upsert an item to the Pinecone index.

        :param item_id: The ID of the item to be upserted.
        :param item_embedding: The embedding of the item.
        :param metadata: Metadata associated with the item.
        """
        index = pinecone.Index(index_name=self.table_name)
        index.upsert([(item_id, item_embedding, metadata)])

    def deinit_pinecone(self) -> None:
        """Deinitialize Pinecone to free up resources."""
        pinecone.deinit()