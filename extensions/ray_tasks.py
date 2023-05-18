import sys
import logging
import ray
from collections import deque
from typing import Dict, List

from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))
from extensions.ray_objectives import CooperativeObjectivesListStorage

try:
    ray.init(address="auto", namespace="babyagi", logging_level=logging.FATAL, ignore_reinit_error=True)
except:
    ray.init(namespace="babyagi", logging_level=logging.FATAL, ignore_reinit_error=True)

@ray.remote
class CooperativeTaskListStorageActor:
    def __init__(self):
        self.tasks = deque([])

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

    def tasks(self):
        return self.tasks

class CooperativeTaskListStorage:
    def __init__(self, name: str, type: str):
        self.name = name + "_" + type

        try:
            self.actor = ray.get_actor(name=self.name, namespace="babyagi")
        except ValueError:
            self.actor = CooperativeTaskListStorageActor.options(name=self.name, namespace="babyagi", lifetime="detached").remote()

        objectives = CooperativeObjectivesListStorage()
        objectives.append(name)

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

    def tasks(self):
        return ray.get(self.actor.tasks.remote())
