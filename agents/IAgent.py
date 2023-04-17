from collections import deque
from typing import NamedTuple
from vector.weaviate import Weaviate
from .ITask import Task
from agents.browser_agent import BrowserAgent
from agents.logger_agent import LoggerAgent
from completion.openai_provider import OpenAiProvider


class AgentData(NamedTuple):
    objective: str
    active_tasks: deque[Task]
    completed_tasks: list[Task]
    vectordb: Weaviate
    open_ai: OpenAiProvider
    browser: BrowserAgent
    logger: LoggerAgent