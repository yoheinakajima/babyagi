import sys
import logging
import ray
from collections import deque
from typing import Dict, List

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

try:
    ray.init(address="auto", namespace="babyagi", logging_level=logging.FATAL, ignore_reinit_error=True)
except:
    ray.init(namespace="babyagi", logging_level=logging.FATAL, ignore_reinit_error=True)

@ray.remote
class CooperativeTaskListStorageActor:
    def __init__(self, task_list: deque):
        self.tasks = task_list

    def append(self, task: Dict):
        self.tasks.append(task)

    def appendleft(self, task: Dict):
        self.tasks.appendleft(task)

    def replace(self, tasks: List[Dict]):
        self.tasks = deque(tasks)

    def reference(self, index: int):
        return self.tasks[index]

    def pop(self):
        return self.tasks.pop()

    def popleft(self):
        return self.tasks.popleft()

    def is_empty(self):
        return False if self.tasks else True

    def get_tasks(self):
        return self.tasks

class CooperativeTaskListStorage:
    def __init__(self, name: str, task_list: deque):
        self.name = name

        try:
            self.actor = ray.get_actor(name=self.name, namespace="babyagi")
        except ValueError:
            self.actor = CooperativeTaskListStorageActor(task_list).options(name=self.name, namespace="babyagi", lifetime="detached").remote()

    def append(self, task: Dict):
        self.actor.append.remote(task)

    def appendleft(self, task: Dict):
        self.actor.appendleft.remote(task)

    def replace(self, tasks: List[Dict]):
        self.actor.replace.remote(tasks)

    def reference(self, index: int):
        return ray.get(self.actor.reference(index).remote())

    def pop(self):
        return ray.get(self.actor.pop.remote())

    def popleft(self):
        return ray.get(self.actor.popleft.remote())

    def is_empty(self):
        return ray.get(self.actor.is_empty.remote())

    def get_tasks(self):
        return ray.get(self.actor.get_tasks.remote())
