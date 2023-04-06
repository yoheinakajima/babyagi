from helpers import OpenAIHelper

class TaskExecutionAgent:
    def __init__(self, task):
        self.task = task
        self.open_ai_helper = OpenAIHelper()

    def execute(self):
        if self.task.result: raise Exception(f"Tried to execute task \"{self.task.name}\", which has already been executed")
        context=self.task.context_agent.get_context(query=self.task.objective, n=5)
        prompt = f"You are an AI who performs one task based on the following objective: {self.task.objective}.\nTake into account these previously completed tasks: {context}\nYour task: {self.task.name}\nResponse:"
        return self.open_ai_helper.get_model_response(prompt=prompt, temperature=0.7, max_tokens=2000)