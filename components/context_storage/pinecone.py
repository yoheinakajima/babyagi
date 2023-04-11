import os
from typing import Callable, Optional

import openai
from .IContextStorage import ContextStorage, StorageOptions, ContextResult, ContextData

class PineconeOptions(StorageOptions):
    api_key: str
    environment: str
    embedding_method: Callable[[str], list[float]]
    storage_name: str
    clean_storage: bool
    
    @staticmethod
    def _get_ada_embedding(text):
        if not openai.api_key:
            openai.api_key = os.getenv("OPENAI_API_KEY", "")
            if not openai.api_key:
                raise ValueError("OPENAI_API_KEY is missing from .env")
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

    def __init__(
            self,
            embedding_method: Optional[Callable[[str], list[float]]] = None, 
            api_key: Optional[str] = None,
            environment: Optional[str] = None,
            storage_name: Optional[str] = None,
            clean_storage: bool = False
        ) -> None:
        
        if api_key is None:
            api_key = os.getenv("PINECONE_API_KEY", "")
            if not api_key:
                raise ValueError("PINECONE_API_KEY is missing from .env")
            
        if environment is None:
            environment = os.getenv("PINECONE_ENVIRONMENT", "")
            if not environment:
                raise ValueError("PINECONE_ENVIRONMENT is missing from .env")

        self.api_key = api_key
        self.environment = environment
        self.storage_name = os.getenv("PINECONE_STORAGE_NAME", "tasks") if storage_name is None else storage_name
        self.embedding_method = PineconeOptions._get_ada_embedding if embedding_method is None else embedding_method
        self.clean_storage = clean_storage

class PineconeTaskStorage(ContextStorage):
    def __init__(self, options: PineconeOptions = PineconeOptions()):
        try:
            import pinecone
            self.pinecone = pinecone
        except ImportError:
            raise ImportError("Please install pinecone python client: pip install pinecone-client")

        pinecone.init(api_key=options.api_key, environment=options.environment)
        self.storage_name = options.storage_name
        self._create_storage(options.clean_storage)
        self.embedding_method = options.embedding_method
        self.index = pinecone.Index(options.storage_name)

    def _create_storage(self, clean_storage: bool = False) -> None:
        if self._has_storage():
            if not clean_storage:
                return
            self.delete_storage()
        print(f'(pinecone): creating storage index {self.storage_name}')
        self.pinecone.create_index(self.storage_name, 1536)
        
    def _has_storage(self) -> bool:
        return self.storage_name in self.pinecone.list_indexes()
    
    def delete_storage(self) -> None:
        print(f'(pinecone): deleting storage index {self.storage_name}')
        self.pinecone.delete_index(self.storage_name)
    
    def query(self, query: str, fields: list[str] = None, n: int = 1, namespace: str = 'default') -> list[ContextResult]:
        # Generate query embedding
        query_embedding = self.embedding_method(query)

        # Perform search and retrieve results
        results = self.index.query(query_embedding, top_k=n, namespace=namespace, include_metadata=True)
        sorted_results = sorted(results.get('matches', []), key=lambda x: x.score, reverse=True)

        # Transform results into standard format
        transformed_results = []
        for item in sorted_results:
            data = item['metadata']

            # Filter metadata by fields if specified
            if fields is not None:
                data = { key: value for key, value in data.items() if key in fields }

            # Append transformed result to list
            transformed_results.append(ContextResult(item['id'], item['score'], data))

        return transformed_results
    
    def upsert(self, context: ContextData, namespace: str = 'default') -> None:
        vector = self.embedding_method(context.enriched_data)
        self.index.upsert([(context.id, vector, context.data)], namespace)
