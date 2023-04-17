import os

import pinecone

from memories.base import Memory, get_ada_embedding, MemoryQueryResult


class PineconeMemory(Memory):
    def __init__(self, api_key=None, env=None, table_name=None, namespace=None):
        if api_key is None:
            api_key = os.getenv("PINECONE_API_KEY", "")

        assert api_key, "PINECONE_API_KEY environment variable is missing from .env"

        if env is None:
            env = os.getenv("PINECONE_ENVIRONMENT", "")
            assert env, "PINECONE_ENVIRONMENT environment variable is missing from .env"

        pinecone.init(api_key=api_key, environment=env)
        dimension = 1536
        metric = "cosine"
        pod_type = "p1"

        if table_name is None:
            table_name = os.getenv("TABLE_NAME", "")
        assert table_name, "TABLE_NAME environment variable is missing from .env"

        if table_name not in pinecone.list_indexes():
            pinecone.create_index(
                table_name, dimension=dimension, metric=metric, pod_type=pod_type
            )

        # Connect to the index
        self.index = pinecone.Index(table_name)
        self.namespace = namespace

    def query(self, query: str, n: int) -> list:
        return [
            MemoryQueryResult(
                match.id,
                match.score,
                match.metadata,
            ) for match in self.index.query(
                get_ada_embedding(query), top_k=n, include_metadata=True, namespace=self.namespace
            ).matches
        ]

    def add(self, vector_id: str, text: str, metadata: dict) -> None:
        self.index.upsert([(vector_id, get_ada_embedding(text), metadata)], namespace=self.namespace)
