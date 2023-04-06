from helpers import OpenAIHelper

class TaskExecutionAgent:
    def __init__(self, task):
        self.task = task

    def identify(self):
        print('hi')

    def execute(self):
        if self.task.result: raise Exception(f"Tried to execute task \"{self.task.name}\", which has already been executed")
        context=self.task.context_agent.get_context(query=self.task.objective, n=5)
        return OpenAIHelper.get_davinci_response(f"You are an AI who performs one task based on the following objective: {self.task.objective}.\nTake into account these previously completed tasks: {context}\nYour task: {self.task.name}\nResponse:")