import unittest
from typing import Dict
from unittest.mock import MagicMock, patch

from src.agents.context_agent import ContextAgent
from src.utils import get_ada_embedding
import pinecone

class TestContextAgent(unittest.TestCase):

    def setUp(self) -> None:
        """
        Create a clean ContextAgent instance for each test case with a mock configuration.
        """
        self.config: Dict[str, str] = {
            'api_key': 'your_openai_api_key',
            'engine': 'davinci-codex',
            'temperature': 0.5,
            'max_tokens': 50,
        }
        self.index = "test-index"
        self.n = 5
        self.context_agent = ContextAgent(config=self.config, index=self.index, n=self.n)

    def test_init(self) -> None:
        """
        Test that the ContextAgent instance is initialized with the provided configuration.
        """
        self.assertIsInstance(self.context_agent, ContextAgent)
        self.assertEqual(self.context_agent.config, self.config)
        self.assertEqual(self.context_agent.index, self.index)
        self.assertEqual(self.context_agent.n, self.n)

    @patch('src.utils.get_ada_embedding')
    @patch.object(ContextAgent, '_pinecone_query')
    @patch.object(ContextAgent, '_extract_task_list')
    def test_get_relevant_tasks(self, mock_extract_task_list, mock_pinecone_query, mock_get_ada_embedding) -> None:
        """
        Test the get_relevant_tasks method by mocking the related methods and functions.
        """
        query = "Find the best tasks for this objective"
        mock_get_ada_embedding.return_value = [0.1, 0.2, 0.3]
        mock_pinecone_query.return_value = MagicMock()
        mock_extract_task_list.return_value = ["Task 1", "Task 2", "Task 3"]

        relevant_tasks = self.context_agent.get_relevant_tasks(query, self.n)

        self.assertEqual(relevant_tasks, ["Task 1", "Task 2", "Task 3"])
        mock_get_ada_embedding.assert_called_once_with(query)
        mock_pinecone_query.assert_called_once_with(mock_get_ada_embedding.return_value)
        mock_extract_task_list.assert_called_once_with(mock_pinecone_query.return_value)

    # You can add more test cases for the _pinecone_query and _extract_task_list methods if needed.

if __name__ == "__main__":
    unittest.main()
