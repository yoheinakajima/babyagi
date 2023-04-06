import unittest
from typing import Dict, List
from unittest.mock import MagicMock, patch

from src.agents.prioritization_agent import PrioritizationAgent
from src.task_manager import TaskManager

class TestPrioritizationAgent(unittest.TestCase):

    def setUp(self) -> None:
        """
        Create a clean PrioritizationAgent instance for each test case with a mock configuration.
        """
        self.config: Dict[str, str] = {
            'api_key': 'your_openai_api_key',
            'engine': 'davinci-codex',
            'temperature': 0.5,
            'max_tokens': 50,
        }
        self.prioritization_agent = PrioritizationAgent(self.config)

    def test_init(self) -> None:
        """
        Test that the PrioritizationAgent instance is initialized with the provided configuration.
        """
        self.assertIsInstance(self.prioritization_agent, PrioritizationAgent)
        self.assertEqual(self.prioritization_agent.config, self.config)

    @patch.object(PrioritizationAgent, '_get_task_names')
    @patch.object(PrioritizationAgent, '_call')
    @patch.object(PrioritizationAgent, '_parse_response')
    @patch.object(PrioritizationAgent, '_update_task_manager')
    def test_prioritize_tasks(self, mock_update_task_manager, mock_parse_response, mock_call, mock_get_task_names) -> None:
        """
        Test the prioritize_tasks method by mocking the related methods and functions.
        """
        task_manager = TaskManager()
        task_manager.add_task({"task_id": 1, "task_name": "Test Task 1"})
        task_manager.add_task({"task_id": 2, "task_name": "Test Task 2"})

        this_task_id = 1
        objective = "Prioritize tasks according to importance"

        mock_get_task_names.return_value = ["Test Task 1", "Test Task 2"]
        mock_call.return_value = "1. Test Task 2\n2. Test Task 1"
        mock_parse_response.return_value = [{"task_id": 2, "task_name": "Test Task 2"},
                                            {"task_id": 1, "task_name": "Test Task 1"}]

        self.prioritization_agent.prioritize_tasks(this_task_id, objective, task_manager)

        mock_get_task_names.assert_called_once_with(task_manager)
        mock_call.assert_called_once_with(task_names=mock_get_task_names.return_value,
                                          objective=objective, next_task_id=this_task_id+1)
        mock_parse_response.assert_called_once_with(mock_call.return_value)
        mock_update_task_manager.assert_called_once_with(task_manager, mock_parse_response.return_value)

    # You can add more test cases for the _get_task_names, _parse_response, and _update_task_manager methods if needed.

if __name__ == "__main__":
    unittest.main()
