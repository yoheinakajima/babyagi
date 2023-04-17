from abc import ABC, abstractmethod
from typing import NamedTuple

class StorageOptions(NamedTuple):
    host: str

class ContextResult(NamedTuple):
    id: str
    score: float
    data: dict

class ContextData(NamedTuple):
    id: str
    data: dict

class ContextStorage(ABC):

    @abstractmethod
    def __init__(self, options: StorageOptions):
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
