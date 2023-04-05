import os
import time
from collections import deque
from typing import Dict, List

import openai
import pinecone
from dotenv import load_dotenv


class TaskManager:
    def __init__(self):
        # Initialize an empty task list
        self.task_list = deque([])

    def add_task(self, task: Dict):
        # Add a new task to the task list
        self.task_list.append(task)

    def get_next_task(self) -> Dict:
        # Remove and return the first task in the task list
        return self.task_list.popleft() if self.task_list else None

    def has_tasks(self) -> bool:
        # Check if there are tasks in the task list
        return bool(self.task_list)