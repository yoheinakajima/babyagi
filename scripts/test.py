import unittest
from ai import AI
from typing import List

class TestAI(unittest.TestCase):

    def test_task_creation_agent(self):
        ai = AI()
        objective = "Solve world hunger."
        result = {"data": "We need to research sustainable farming methods."}
        task_description = "Research and identify sustainable farming methods."
        task_list = ["Develop a list of potential sustainable farming techniques."]
        
        # Test if task_creation_agent returns a list of new tasks based on the given input
        new_tasks = ai.task_creation_agent(objective, result, task_description, task_list)
        self.assertIsInstance(new_tasks, list)
        self.assertNotEqual(len(new_tasks), 0)
        
    def test_prioritization_agent(self):
        ai = AI()
        this_task_id = 3
        ai.task_list = [{"task_id": 1, "task_name": "Task 1"},
                        {"task_id": 2, "task_name": "Task 2"},
                        {"task_id": 4, "task_name": "Task 4"}]

        # Test if prioritization_agent reorders the task list correctly
        ai.prioritization_agent(this_task_id)
        self.assertEqual(ai.task_list[0]["task_id"], 3)
        self.assertEqual(ai.task_list[1]["task_id"], 4)

    def test_execution_agent(self):
        ai = AI()
        objective = "Solve world hunger."
        task = "Develop a list of potential sustainable farming techniques."

        # Test if execution_agent generates a result based on the given input
        result = ai.execution_agent(objective, task)
        self.assertIsInstance(result, str)
        self.assertNotEqual(len(result), 0)

    def test_context_agent(self):
        ai = AI()
        query = "Solve world hunger."
        index = "quickstart"
        n = 5

        # Test if context_agent retrieves the relevant context based on the query
        context = ai.context_agent(query, index, n)
        self.assertIsInstance(context, list)
        self.assertEqual(len(context), n)

if __name__ == "__main__":
    unittest.main()