from collections import deque
from typing import Dict, Union
from functools import wraps


def task_format_validation(add_task_func):
    @wraps(add_task_func)
    def wrapper(self, task: Dict[str, Union[str, Dict]]):
        if not isinstance(task, Dict):
            raise TypeError("Task must be a dictionary.")
        if 'task_name' not in task:
            raise KeyError("Task must have a 'task_name' key.")
        add_task_func(self, task)
    return wrapper


class TaskManager:
    def __init__(self) -> None:
        """
        Initialize an empty task list using deque from the collections module.
        """
        self.task_list = deque([])

    @task_format_validation
    def add_task(self, task: Dict[str, Union[str, Dict]]) -> None:
        """
        Add a new task to the task list.

        :param task: A dictionary containing task information.
        :return: None
        """
        self.task_list.append(task)

    def get_next_task(self) -> Union[Dict[str, Union[str, Dict]], None]:
        """
        Remove and return the first task in the task list.

        :return: A dictionary containing task information or None if the task list is empty.
        """
        return self.task_list.popleft() if self.task_list else None

    def has_tasks(self) -> bool:
        """
        Check if there are tasks in the task list.

        :return: True if the task list has tasks, False otherwise.
        """
        return bool(self.task_list)

    def __len__(self) -> int:
        """
        Return the number of tasks in the task list.

        :return: An integer representing the number of tasks.
        """
        return len(self.task_list)

    def __getitem__(self, index: int) -> Dict[str, Union[str, Dict]]:
        """
        Get a task by its index in the task list.

        :param index: The index of the task in the task list.
        :return: A dictionary containing the task information.
        """
        return self.task_list[index]

    def __str__(self) -> str:
        """
        Return a string representation of the task list.

        :return: A formatted string representing the tasks in the task list.
        """
        tasks = [f"{index + 1}. {task['task_name']}" for index,
                 task in enumerate(self.task_list)]
        return '\n'.join(tasks)
