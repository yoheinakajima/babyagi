import unittest
from typing import Dict
from unittest.mock import MagicMock, patch

# Use a relative import for the BaseAgent class
from src.agents.base_agent import BaseAgent

class TestBaseAgent(unittest.TestCase):

    def setUp(self) -> None:
        """
        Create a clean BaseAgent instance for each test case with a mock configuration.
        """
        self.config: Dict[str, str] = {
            'api_key': 'your_openai_api_key',
            'engine': 'davinci-codex',
            'temperature': 0.5,
            'max_tokens': 50,
        }
        self.base_agent = BaseAgent(self.config)

    def test_init(self) -> None:
        """
        Test that the BaseAgent instance is initialized with the provided configuration.
        """
        self.assertIsInstance(self.base_agent, BaseAgent)
        self.assertEqual(self.base_agent.config, self.config)

    @patch('openai.Completion.create')
    def test_call(self, mock_completion_create: MagicMock) -> None:
        """
        Test the __call__ method by mocking the openai.Completion.create function.
        """
        mock_completion_create.return_value.choices = [{'text': 'Mocked response'}]

        objective = "Write a Python function to calculate the sum of two numbers."
        task = "Function: sum(a: int, b: int) -> int"
        context = "Relevant context"
        response = self.base_agent(objective=objective, task=task, context=context)

        self.assertEqual(response, 'Mocked response')
        mock_completion_create.assert_called_once()

if __name__ == "__main__":
    unittest.main()
