import unittest
from src.agents.context_agent import ContextAgent
from src.agents.prioritization_agent import PrioritizationAgent
from src.agents.task_creation_agent import TaskCreationAgent
from src.task_manager import TaskManager

class TestAgentsIntegration(unittest.TestCase):

    def setUp(self) -> None:
        """
        Set up the necessary agents and TaskManager for the integration tests.
        """
        self.config = {
            'api_key': 'your_openai_api_key',
            'engine': 'davinci-codex',
            'temperature': 0.5,
            'max_tokens': 50,
        }
        self.context_agent = ContextAgent(self.config, "pinecone_index")
        self.prioritization_agent = PrioritizationAgent(self.config)
        self.task_creation_agent = TaskCreationAgent(self.config)
        self.task_manager = TaskManager()

    def test_agents_interaction(self) -> None:
        """
        Test the interaction between different agents and the task manager.
        """
        # Add some initial tasks to the task manager
        self.task_manager.add_task({"task_name": "Initial Task 1"})
        self.task_manager.add_task({"task_name": "Initial Task 2"})

        # Simulate ContextAgent interaction
        query = "example query for context"
        relevant_tasks = self.context_agent.get_relevant_tasks(query, 5)
        self.assertIsInstance(relevant_tasks, list)

        # Simulate PrioritizationAgent interaction
        self.prioritization_agent.prioritize_tasks(1, "Prioritize tasks", self.task_manager)

        # Check if the prioritized tasks are added to the task manager
        self.assertGreater(len(self.task_manager.task_list), 2)

        # Simulate TaskCreationAgent interaction
        objective = "Create new tasks based on the previous result"
        result = {"result_text": "Result of the last completed task"}
        task_description = "Description of the last completed task"

        new_tasks = self.task_creation_agent.create_tasks(objective, result, task_description, self.task_manager)

        # Check if new tasks are created
        self.assertIsInstance(new_tasks, list)
        self.assertGreater(len(new_tasks), 0)

        # Add the new tasks to the task manager
        for task in new_tasks:
            self.task_manager.add_task(task)

        # Check if the new tasks are added to the task manager
        self.assertGreater(len(self.task_manager.task_list), len(new_tasks) + 2)

if __name__ == "__main__":
    unittest.main()
