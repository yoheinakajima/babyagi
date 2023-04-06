import unittest
from typing import Dict, List
from unittest.mock import MagicMock, patch

from src.agents.task_creation_agent import TaskCreationAgent
from src.task_manager import TaskManager

class TestTaskCreationAgent(unittest.TestCase):

    def setUp(self) -> None:
        """
        Create a clean TaskCreationAgent instance for each test case with a mock configuration.
        """
        self.config: Dict[str, str] = {
            'api_key': 'your_openai_api_key',
            'engine': 'davinci-codex',
            'temperature': 0.5,
            'max_tokens': 50,
            'prompt': "Objective: {objective}\nResult: {result}\nTask Description: {task_description}\nTask List: {task_list}\n\n",
        }
        self.task_creation_agent = TaskCreationAgent(self.config)

    def test_init(self) -> None:
        """
        Test that the TaskCreationAgent instance is initialized with the provided configuration.
        """
        self.assertIsInstance(self.task_creation_agent, TaskCreationAgent)
        self.assertEqual(self.task_creation_agent.config, self.config)

    @patch.object(TaskCreationAgent, '_get_task_list')
    @patch.object(TaskCreationAgent, '_call')
    @patch.object(TaskCreationAgent, '_parse_response')
    def test_create_tasks(self, mock_parse_response, mock_call, mock_get_task_list) -> None:
        """
        Test the create_tasks method by mocking the related methods and functions.
        """
        task_manager = TaskManager()
        task_manager.add_task({"task_name": "Test Task 1"})
        task_manager.add_task({"task_name": "Test Task 2"})

        objective = "Generate new tasks based on the previous result"
        result = {"result_text": "Result of the last completed task"}
        task_description = "Description of the last completed task"

        mock_get_task_list.return_value = ["Test Task 1", "Test Task 2"]
        mock_call.return_value = "New Task 1\nNew Task 2\nNew Task 3"
        mock_parse_response.return_value = [{"task_name": "New Task 1"},
                                            {"task_name": "New Task 2"},
                                            {"task_name": "New Task 3"}]

        new_tasks = self.task_creation_agent.create_tasks(objective, result, task_description, task_manager)

        mock_get_task_list.assert_called_once_with(task_manager)
        mock_call.assert_called_once_with(objective=objective, result=result,
                                          task_description=task_description,
                                          task_list=', '.join(mock_get_task_list.return_value))
        mock_parse_response.assert_called_once_with(mock_call.return_value)
        self.assertEqual(new_tasks, mock_parse_response.return_value)

    # You can add more test cases for the _get_task_list and _parse_response methods if needed.

if __name__ == "__main__":
    unittest.main()
