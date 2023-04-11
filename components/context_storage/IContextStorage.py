from abc import ABC, abstractmethod
from typing import NamedTuple

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
    def __init__(self, options: StorageOptions):
        pass

    @abstractmethod
    def delete_storage(self) -> None:
        pass

    @abstractmethod
    def query(self, query: str, fields: list[str] = [], n: int = 1) -> list[ContextResult]:
        pass

    @abstractmethod
    def upsert(self, context: ContextData, namespace: str = 'default') -> None:
        pass