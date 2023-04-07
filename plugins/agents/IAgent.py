from abc import ABC, abstractmethod
from typing import NamedTuple
from collections import deque

from ..vectors.IVectorDB import VectorDB
from ..completions.ICompletionClient import CompletionClient


class Task(NamedTuple):
    id: int
    description: str = ""
    result: str = ""

class AgentData(NamedTuple):
    objective: str
    active_tasks: deque[Task]
    completed_tasks: list[Task]
    vectordb: VectorDB
    completion_client: CompletionClient

class Agent(ABC):
    @abstractmethod
    def exec(data: AgentData) -> AgentData:
        pass
