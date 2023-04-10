from collections import deque
from typing import Dict, List, Union

class Task:
    def __init__(self, task_id: int, task_name: str):
        self.task_id = task_id
        self.task_name = task_name
        self.completed = False
        self.result = None
    
    def complete(self, result):
        self.result = result
        self.completed = True

class TaskManager:
    def __init__(self, task_list: List[Task] = None):
        self.task_list = task_list or []

    def add_task(self, task: Task):
        self.task_list.append(task)

    def get_next_task(self) -> Union[Task, None]:
        if self.has_tasks():
            return self.task_list.pop(0)
        return None

    def has_tasks(self) -> bool:
        return len(self.task_list) > 0
    
    def get_tasks(self) -> List[Task]:
        return self.task_list
    
