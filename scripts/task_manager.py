from collections import deque
from typing import Dict, List, Union

class TaskManager:
    def __init__(self) -> None:
        """
        Initialize an empty task list using deque from the collections module.
        """
        self.task_list = deque([])

    def add_task(self, task: Dict) -> None:
        """
        Add a new task to the task list.

        :param task: A dictionary containing task information.
        :return: None
        """
        self.task_list.append(task)

    def get_next_task(self) -> Union[Dict, None]:
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

    def __str__(self) -> str:
        """
        Return a string representation of the task list.

        :return: A formatted string representing the tasks in the task list.
        """
        tasks = [f"{index + 1}. {task['task_name']}" for index, task in enumerate(self.task_list)]
        return '\n'.join(tasks)