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

    @patch("openai.Embedding.create")
    @patch.object(ContextAgent, '_pinecone_query')
    @patch.object(ContextAgent, '_extract_task_list')
    def test_get_relevant_tasks(self, mock_extract_task_list, mock_pinecone_query, mock_embedding_create: MagicMock) -> None:
        """
        Test the get_relevant_tasks method by mocking the related methods and functions.
        """
        # Mock the embedding create response
        mock_embedding_create.return_value = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3]
                }
            ]
        }

        query = "Find the best tasks for this objective"
        mock_pinecone_query.return_value = MagicMock()
        mock_extract_task_list.return_value = ["Task 1", "Task 2", "Task 3"]

        relevant_tasks = self.context_agent.get_relevant_tasks(query, self.n)

        self.assertEqual(relevant_tasks, ["Task 1", "Task 2", "Task 3"])
        mock_embedding_create.assert_called_once_with(input=[query], model="text-embedding-ada-002")
        mock_pinecone_query.assert_called_once_with(mock_embedding_create.return_value["data"][0]["embedding"])
        mock_extract_task_list.assert_called_once_with(mock_pinecone_query.return_value)

        # You can add more test cases for the _pinecone_query and _extract_task_list methods if needed.

if __name__ == "__main__":
    unittest.main()
