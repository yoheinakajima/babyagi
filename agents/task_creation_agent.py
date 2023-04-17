import itertools
from agents.IAgent import AgentData
from agents.ITask import Task


class TaskCreationAgent:
    def __init__(self):
        pass
    

    def create_first_task(self, agent: AgentData):
        prompt = f"""
            You are a task creation AI that creates a task with the following objective: {agent.objective}.
            Your job is to return the very first task for this objective
            Return the very generic task as a string."""

        response = agent.open_ai.generate_text(prompt)
        agent.logger.log(f"First Task: {response}")
        agent.active_tasks.append(Task(id=1, description=response))


    def create_tasks(self, last_task: Task, agent: AgentData):
        complete_string = " AND ".join(complete.description for complete in agent.completed_tasks)

        prompt = f"""
            You are a task creation AI that uses the result of an execution agent to create new tasks with the following final objective: {agent.objective}.
            The last completed task has the result: {last_task.result}.
            This result was based on this task description: {last_task.description}.

            Based on that result return a prioritized array of up to 3 CONCISE tasks, they should not overlap with any previous tasks mentioned in {complete_string} and should contribute to the advancement of our objective.
            Please be very precise and include important information such as URLs or names into the task."""

        response = agent.open_ai.generate_text(prompt)
        agent.logger.log(f"New Tasks: {response}")

        new_tasks = response.split("\n") if "\n" in response else [response]
        
        id_iter = itertools.count(start=last_task.id)
        new_tasks_arr = [Task(id=next(id_iter), description=task) for task in new_tasks]

        agent.active_tasks.clear()
        agent.active_tasks.extend(new_tasks_arr)