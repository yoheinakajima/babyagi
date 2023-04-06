from agents import ContextAgent
from helpers import OpenAIHelper

class Task:
    def __init__(self, id: int, name: str, context_agent: ContextAgent):
        self.id = id
        self.name = name
        self.result = None
        self.context_agent = context_agent
        self.open_ai_helper = OpenAIHelper()
        self.objective = self.context_agent.get_objective()
        if not self.name:
            raise ValueError("Task name cannot be empty")

    def print_self(self):
        print(self.to_string())

    def to_string(self):
        return f"{self.id}\t{self.name}\t{self.result}"
    
    def execute(self):
        if self.result: raise Exception(f"Tried to execute task \"{self.name}\", which has already been executed")
        context=self.context_agent.get_context(query=self.objective, n=5)
        prompt = f"You are an AI who performs one task based on the following objective: {self.objective}.\nTake into account these previously completed tasks: {context}\nYour task: {self.name}\nResponse:"
        self.result = self.open_ai_helper.get_model_response(prompt = prompt)