import itertools
from agents.IAgent import AgentData
from agents.ITask import Task


class TaskCreationAgent:
    def __init__(self):
        pass
    
    def create_first_task(self, agent: AgentData):
        # Generate prompt for OpenAI completion
        
        prompt = f"""
        You are a task creation AI that creates a task with the following objective: {agent.objective}.
        Your job is to return the very first task for this objective
        Return the very generic task as a string."""

        agent.logger.log(f"Executing: {prompt}")
        response = agent.open_ai.generate_text(prompt)
        agent.logger.log(f"Solving: {response}")

        #new_tasks = response.split("\n") if "\n" in response else [response]
        agent.active_tasks.append(Task(id=1, description=response))

    def create_tasks(self, last_task: Task, agent: AgentData, warning: str):
        # Generate prompt for OpenAI completion
        
        tasks = []
        for task in agent.active_tasks:
            tasks.append(task.description)

        description_string = "AND ".join(task4.description for task4 in agent.completed_tasks)

        prompt = f"""
        You are a task creation AI that uses the result of an execution agent to create new tasks with the following final objective: {agent.objective}.
        The last completed task has the result: {last_task.result}.
        This result was based on this task description: {last_task.description}.

        Based on that result return a prioritized array of up to 3 CONCISE tasks, they should not overlap with any previous tasks mentioned in {description_string} and should contribute to the advancement of our objective.
        Please be very precise and include important information such as URLs or names into the task."""

        #agent.logger.log(f"New Tasks Prompt: {prompt}")
        response = agent.open_ai.generate_text(prompt)
        agent.logger.log(f"New Tasks: {response}")

        new_tasks = response.split("\n") if "\n" in response else [response]

        start_value = last_task.id
        id_iter = itertools.count(start=start_value)
        tasks2 = [Task(id=next(id_iter), description=task) for task in new_tasks]

        agent.active_tasks.clear()
        agent.active_tasks.extend(tasks2)
