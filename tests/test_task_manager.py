import unittest
from typing import Dict
from src.task_manager import TaskManager

class TestTaskManager(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create a clean TaskManager instance for each test case.
        """
        self.task_manager = TaskManager()

    def test_add_task(self) -> None:
        """
        Test the add_task method with valid input.
        """
        task: Dict[str, str] = {"task_id": 1, "task_name": "Test Task"}
        self.task_manager.add_task(task)
        self.assertEqual(len(self.task_manager), 1)
        self.assertEqual(self.task_manager[0], task)

    def test_add_task_invalid(self) -> None:
        """
        Test the add_task method with invalid input.
        """
        task: Dict[str, str] = {"invalid_key": 1, "task_name": "Test Task"}
        with self.assertRaises(ValueError):
            self.task_manager.add_task(task)

    def test_get_next_task(self) -> None:
        """
        Test the get_next_task method when tasks are available.
        """
        task1: Dict[str, str] = {"task_id": 1, "task_name": "Test Task 1"}
        task2: Dict[str, str] = {"task_id": 2, "task_name": "Test Task 2"}
        self.task_manager.add_task(task1)
        self.task_manager.add_task(task2)
        next_task = self.task_manager.get_next_task()
        self.assertEqual(next_task, task1)

    def test_get_next_task_empty(self) -> None:
        """
        Test the get_next_task method when the task list is empty.
        """
        with self.assertRaises(IndexError):
            self.task_manager.get_next_task()

if __name__ == "__main__":
    unittest.main()
