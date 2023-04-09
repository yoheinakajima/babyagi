from abc import ABC, abstractmethod
from enum import Enum
from typing import NamedTuple, Callable

class PineconeOptions(NamedTuple):
    api_key: str
    environment: str
    embedding_method: Callable[[str], list[float]]
    storage_name: str = 'tasks'
    clean_storage: bool = False

class WeaviateOptions(NamedTuple):
    host: str = 'http://localhost:8080'
    vectorizer: str = 'text2vec-transformers'
    storage_name: str = 'tasks'
    clean_storage: bool = False


class ContextResult(NamedTuple):
    id: str
    score: float
    data: dict

class ContextData(NamedTuple):
    id: str
    data: dict
    enriched_data: str

class StorageType(Enum):
    PINECONE = 'pinecone'
    WEAVIATE = 'weaviate'

class ContextStorage(ABC):
    @abstractmethod
    def delete_storage(self) -> None:
        pass

    @abstractmethod
    def query(self, query: str, fields: list[str] = [], n: int = 1, namespace: str = 'default') -> list[ContextResult]:
        pass

    @abstractmethod
    def upsert(self, context: ContextData, namespace: str = 'default') -> None:
        pass

    @staticmethod
    def factory(storage_type: StorageType, options: PineconeOptions | WeaviateOptions) -> 'ContextStorage':
        if not isinstance(storage_type, StorageType):
            if isinstance(storage_type, str):
                storage_type = StorageType(storage_type)
            else:
                raise ValueError('Invalid storage type.')
        
        if storage_type == StorageType.PINECONE:
            from .pinecone import PineconeTaskStorage
            return PineconeTaskStorage(options)
        
        if storage_type == StorageType.WEAVIATE:
            from .weaviate import WeaviateTaskStorage
            return WeaviateTaskStorage(options)
