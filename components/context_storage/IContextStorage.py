from abc import ABC, abstractmethod
from typing import NamedTuple, Optional

class StorageOptions(NamedTuple):
    pass

class ContextResult(NamedTuple):
    id: str
    score: float
    data: dict

class ContextData(NamedTuple):
    id: str
    data: dict
    enriched_data: str

class ContextStorage(ABC):

    @abstractmethod
    def __init__(self, storage_name: Optional[str] = None, options: StorageOptions):
        pass

    @abstractmethod
    def delete_storage(self) -> None:
        pass

    @abstractmethod
    def query(self, query: str, fields: list[str] = [], n: int = 1, namespace: str = None) -> list[ContextResult]:
        pass

    @abstractmethod
    def upsert(self, context: ContextData, namespace: str = 'default') -> None:
        pass


def get_storage(storage_type_name: str, task_storage_name: str, options: Optional[StorageOptions]) -> ContextStorage:
    if storage_type_name == 'pinecone':
        from .pinecone import Pinecone
        options = Pinecone.PineconeOptions(storage_name=task_storage_name) if options is None else options
        return Pinecone(options=options)
    if storage_type_name == 'weaviate':
        from .weaviate import Weaviate
        options = Weaviate.WeaviateOptions(storage_name=task_storage_name) if options is None else options
        return Weaviate(options=options)
    else:
        raise ValueError(f'Invalid storage type: {storage_type_name}