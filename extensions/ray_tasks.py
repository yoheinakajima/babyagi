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
        self.task_id_counter = 0

    def append(self, task: Dict):
        self.tasks.append(task)

    def replace(self, tasks: List[Dict]):
        self.tasks = deque(tasks)

    def popleft(self):
        return self.tasks.popleft()

    def is_empty(self):
        return False if self.tasks else True

    def next_task_id(self):
        self.task_id_counter += 1
        return self.task_id_counter

    def get_task_names(self):
        return [t["task_name"] for t in self.tasks]

class CooperativeTaskListStorage:
    def __init__(self, name: str):
        self.name = name

        try:
            self.actor = ray.get_actor(name=self.name, namespace="babyagi")
        except ValueError:
            self.actor = CooperativeTaskListStorageActor.options(name=self.name, namespace="babyagi", lifetime="detached").remote()

        objectives = CooperativeObjectivesListStorage()
        objectives.append(self.name)

    def append(self, task: Dict):
        self.actor.append.remote(task)

    def replace(self, tasks: List[Dict]):
        self.actor.replace.remote(tasks)

    def popleft(self):
        return ray.get(self.actor.popleft.remote())

    def is_empty(self):
        return ray.get(self.actor.is_empty.remote())

    def next_task_id(self):
        return ray.get(self.actor.next_task_id.remote())

    def get_task_names(self):
        return ray.get(self.actor.get_task_names.remote())
