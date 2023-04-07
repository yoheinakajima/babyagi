from .base_agent import BaseAgent
from .context_agent import ContextAgent
from typing import Dict

class ExecutionAgent(BaseAgent):
    def __init__(self, config: Dict, context_agent: ContextAgent):
        """
        Initialize an ExecutionAgent instance with its configuration and an instance of ContextAgent.

        :param config: A dictionary containing agent configuration.
        :param context_agent: An instance of the ContextAgent class.
        """
        super().__init__(config)
        self.context_agent = context_agent

    def execute_task(self, objective: str, task: str, n: int = 5) -> str:
        """
        Executes a task based on the given objective and task description.

        :param objective: The overall objective for the AI system.
        :param task: A specific task to be executed by the AI system.
        :param n: Number of top tasks to retrieve. Default is 5.
        :return: A string representing the result of the task execution by the AI agent.
        """
        context = self.context_agent.get_relevant_tasks(query=objective, n=n)
        response_text = self.__call__(objective=objective, task=task, context=context)
        return response_text