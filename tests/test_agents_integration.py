import unittest
from unittest.mock import MagicMock, patch
from src.agents.base_agent import BaseAgent
from src.agents.context_agent import ContextAgent
from src.task_manager import TaskManager

class TestAgentsIntegration(unittest.TestCase):
    def setUp(self) -> None:
        """
        Create a clean instance of the TaskManager, BaseAgent, and ContextAgent for each test case with mock configurations.
        """
        self.config_base_agent = {
            "api_key": "your_openai_api_key",
            "engine": "davinci-codex",
            "temperature": 0.5,
            "max_tokens": 50,
            "prompt": "Objective: {objective}\nTask: {task}\nContext: {context}\n\nOutput:"
        }
        self.config_context_agent = {
            "api_key": "your_openai_api_key",
            "engine": "davinci-codex",
            "temperature": 0.5,
            "max_tokens": 50,
            "index": "test-index",
            "n": 5,
        }
        self.task_manager = TaskManager()
        self.base_agent = BaseAgent(self.config_base_agent)
        self.context_agent = ContextAgent(
            config=self.config_context_agent,
            index=self.config_context_agent["index"],
            n=self.config_context_agent["n"],
        )

    @patch("openai.Completion.create")
    @patch("src.agents.context_agent.ContextAgent._pinecone_query")
    @patch("openai.Embedding.create")
    def test_agents_interaction(self, mock_embedding_create: MagicMock, mock_pinecone_query: MagicMock, mock_completion_create: MagicMock):
        """
        Test the interaction between different agents and the task manager.
        """
        # Add initial tasks
        self.task_manager.add_task({"task_id": 1, "task_name": "Initial Task 1"})
        self.task_manager.add_task({"task_id": 2, "task_name": "Initial Task 2"})
        self.task_manager.add_task({"task_id": 3, "task_name": "Initial Task 3"})

        # Mock the OpenAI API completion response
        mock_completion_create.return_value = MagicMock(choices=[MagicMock(text="def add(a, b):\n    return a + b")])

        # Mock the embedding create response
        mock_embedding_create.return_value = {
            "data": [
                {
                    "embedding": [0.1, 0.2, 0.3]
                }
            ]
        }

        # Mock the Pinecone query response
        mock_pinecone_query.return_value = MagicMock(matches=[
            MagicMock(score=0.9, metadata={"task": "Task 4"}),
            MagicMock(score=0.8, metadata={"task": "Task 5"}),
            MagicMock(score=0.7, metadata={"task": "Task 6"}),
            MagicMock(score=0.6, metadata={"task": "Task 7"}),
            MagicMock(score=0.5, metadata={"task": "Task 8"}),
        ])


        # Query for relevant tasks
        query = "Find the best tasks for this objective"
        relevant_tasks = self.context_agent.get_relevant_tasks(query, 5)


        # Add relevant tasks to the task manager
        for task in relevant_tasks:
            self.task_manager.add_task({"task_id": len(self.task_manager.get_tasks()) + 1, "task_name": task})


        # Check the total number of tasks
        self.assertEqual(len(self.task_manager.get_tasks()), 8)

        # Select a task to complete
        task_to_complete = self.task_manager[4]


        # Complete the task using the BaseAgent
        objective = "Write a Python function to calculate the sum of two numbers."
        task = f"Function: {task_to_complete['task_name']}"
        context = "Relevant context"
        response = self.base_agent(objective=objective, task=task, context=context)

        # Check the response
        self.assertIsNotNone(response)


if __name__ == "__main__":
    unittest.main()
