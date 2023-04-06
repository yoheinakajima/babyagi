# pinecone_helper.py
import pinecone
from typing import List, Tuple


class PineconeHelper:
    def __init__(self, config: dict) -> None:
        """
        Initialize Pinecone helper with the given configuration.

        :param config: A dictionary containing Pinecone configuration settings.
        """
        self.api_key = config['pinecone']['api_key']
        self.environment = config['pinecone']['environment']
        self.dimension = config['pinecone'].get('dimension', 512)
        self.metric = config['pinecone'].get('metric', 'euclidean')
        self.pod_type = config['pinecone'].get('pod_type', 'large')
        self.table_name = config['pinecone']['pinecone_index']['table_name']

        pinecone.init(api_key=self.api_key, environment=self.environment)

        if self.table_name not in pinecone.list_indexes():
            pinecone.create_index(self.table_name, dimension=self.dimension, metric=self.metric, pod_type=self.pod_type)

        self.index = pinecone.Index(self.table_name)

    def upsert(self, items: List[Tuple[str, any, dict]]) -> None:
        """
        Upsert items into the Pinecone index.

        :param items: A list of tuples containing item ID, item vector, and item metadata.
        """
        self.index.upsert(items)


