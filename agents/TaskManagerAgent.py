from typing import Dict
from collections import deque
from agents import ContextAgent
import pinecone
import os

from models import Task
from helpers import OpenAIHelper

class TaskManagerAgent:
    def __init__(self, first_task, objective):
        self.task_list = deque([])
        self.open_ai_helper = OpenAIHelper()
        self.objective = objective
        self.remove_similar_tasks = True
        self.pinecone_table = os.getenv("TABLE_NAME", "")
        if not self.pinecone_table:
            raise Exception("Pinecone table name is missing from .env")
        self.pinecone_index = pinecone.Index(index_name=self.pinecone_table)
        self.context_agent = ContextAgent(self.pinecone_index, objective)
        self.id_counter = 0
        self.add_task(first_task)
        self.objective = objective

    def run(self):
        # Print the task list
        print("\033[95m\033[1m"+"\n*****TASK LIST*****\n"+"\033[0m\033[0m")
        self.print_tasks()

        # Step 1: Pull the first task
        task = self.task_list.popleft()
        print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
        task.print_self()

        # Send to execution function to complete the task based on the context
        task.execute()
        if not task.result: raise Exception("Task did not return a result")
        result = task.result
        print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
        print(result)

        # Step 2: Enrich result and store in Pinecone
        enriched_result = {'data': result}  # This is where you should enrich the result if needed
        result_id = f"result_{task.id}"
        vector = enriched_result['data']  # extract the actual result from the dictionary
        self.pinecone_index.upsert([(result_id, self.open_ai_helper.get_ada_embedding(vector),{"task":task.name,"result":result})])

        # Step 3: Create new tasks and reprioritize task list
        self.create_tasks(enriched_result, task.name)

        self.prioritize(task.id)

    def add_task(self, task: str):
        # make sure that we're getting a string, print out what we have and the type if not
        if not isinstance(task, str):
            print("Task is not a string")
            print(task)
            print(type(task))
            exit()
        self.id_counter += 1 # TODO: should we be starting at 0 instead of 1?
        self.task_list.append(Task(self.id_counter, task, self.context_agent))

    def print_tasks(self):
        for task in self.task_list: task.print_self()

    def create_tasks(self, result: Dict, task_description: str):
        prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {self.objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join([t.to_string() for t in self.task_list])}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
        # response = openai.Completion.create(engine="text-davinci-003",prompt=prompt,temperature=0.5,max_tokens=100,top_p=1,frequency_penalty=0,presence_penalty=0)
        new_tasks = self.open_ai_helper.get_model_response(prompt = prompt).split('\n')
        for t in new_tasks: self.add_task(t)

    def prioritize(self, this_task_id:int):
        task_names = [t.name for t in self.task_list]
        next_task_id = int(this_task_id)+1
        removal_string = "Remove any duplicate/extremely similar tasks." if self.remove_similar_tasks else "Do not remove any tasks."
        prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{self.objective}. {removal_string} Return the result as a numbered list, like:
        #. First task
        #. Second task
        Start the task list with number {next_task_id}."""
        # response = openai.Completion.create(engine="text-davinci-003",prompt=prompt,temperature=0.5,max_tokens=1000,top_p=1,frequency_penalty=0,presence_penalty=0)
        new_tasks = self.open_ai_helper.get_model_response(prompt = prompt).split('\n')
        self.task_list = deque()
        for task_string in new_tasks:
            if '.' in task_string:
                task_parts = task_string.split(".", 1)
            elif ':' in task_string:
                task_parts = task_string.split(":", 1)
            else:
                raise Exception(f"Task string {task_string} does not contain a period or colon. This functionality needs to be improved.")
            if len(task_parts) == 2:
                self.task_list.append(Task(task_parts[0].strip(), task_parts[1].strip(), self.context_agent))