from .IAgent import Agent, Task, AgentData
import re

class TaskCreationAgent(Agent):
    def exec(self, data: AgentData) -> AgentData:
        task_descriptions = [t.description for t in data.active_tasks]
        prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {data.objective}, The last completed task has the result: {data.completed_tasks[-1].result}. This result was based on this task description: {data.completed_tasks[-1].description}. These are incomplete tasks: {', '.join(task_descriptions)}. Based on the result, create new tasks to be completed by the AI system that are not similar to incomplete tasks. Return the tasks as unordered list. If the result of the last completed task was a list, return that instead. If no tasks are needed based on the last task's result, then return nothing."

        response = data.completion_client.text_completion(prompt, max_tokens = 100)
        new_tasks = self.get_new_tasks(response, data)
        data.active_tasks.extend(new_tasks)
        return data 
    
    def get_next_task_id(self, data: AgentData) -> int:
        if(data.active_tasks):
            return max([t.id for t in data.active_tasks]) + 1
        elif(data.completed_tasks):
            return max([t.id for t in data.completed_tasks]) + 1
        return 0
    
    def get_new_tasks(self, response: str, data: AgentData) -> list[str]:
        new_tasks = []
        next_task_id = self.get_next_task_id(data)
        for task in response.split('\n'):
            # remove ordered and unordered list prefixes
            task = re.sub(r'(\d+\s*\.)|(\s*\-\s*)', '', task)
            new_tasks.append(Task(next_task_id, task.strip()))
            next_task_id += 1
        return new_tasks
