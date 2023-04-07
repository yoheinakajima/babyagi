from .IAgent import Agent, Task, AgentData
from collections import deque
import re

class TaskPrioritizationAgent(Agent):
    def exec(self, data: AgentData) -> AgentData:
        task_names = [t.description for t in data.active_tasks]
        prompt = f"""You are an task prioritization AI tasked with removing the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{data.objective}. Do not remove any tasks. Return the result as only the task descriptions one per line, like:
        A task.
        Another task
        """
        response = data.completion_client.text_completion(prompt)
        new_tasks = response.split('\n')
        task_list = deque()
        next_task_id = min([t.id for t in data.active_tasks])
        for task_string in new_tasks:
            task_string = re.sub(r'\d+\s*\.', '', task_string)
            if(task_string.strip()):
                task = Task(next_task_id, task_string.strip())
                task_list.append(task)
                next_task_id += 1
        data.active_tasks.clear()
        data.active_tasks.extend(task_list)
        return data