from .IAgent import Agent, AgentData

class TaskExecutionAgent(Agent):
    def exec(self, data: AgentData) -> AgentData:
        current_task = data.active_tasks.popleft()
        context = data.vectordb.query_table(current_task.description, n = 5)
        prompt =f"You are an AI who performs one task based on the following objective: {data.objective}.\nTake into account these previously completed tasks: {context}\nYour task: {current_task.description}\nResponse:"
        response = data.completion_client.text_completion(prompt, 0.7, 2000)
        current_task = current_task._replace(result = response)
        data.completed_tasks.append(current_task)
        return data