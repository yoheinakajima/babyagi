import openai
import pinecone
import time
from collections import deque
from typing import Dict, List
from dotenv import load_dotenv
import os

load_dotenv()

REMOVE_SIMILAR_TASKS = True

# Set API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env from .env"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Table config
YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert YOUR_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

# Project config
OBJECTIVE = os.getenv("OBJECTIVE", "")
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env"

YOUR_FIRST_TASK = os.getenv("FIRST_TASK", "")
assert YOUR_FIRST_TASK, "FIRST_TASK environment variable is missing from .env"

#Print OBJECTIVE
print("\033[96m\033[1m"+"\n*****OBJECTIVE*****\n"+"\033[0m\033[0m")
print(OBJECTIVE)

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = YOUR_TABLE_NAME
dimension = 1536
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

# Connect to the index
index = pinecone.Index(table_name)

# def add_task(task: Dict):
#     task_list.append(task)

def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

def context_agent(query: str, index: str, n: int):
    query_embedding = get_ada_embedding(query)
    index = pinecone.Index(index_name=index)
    results = index.query(query_embedding, top_k=n, include_metadata=True)
    #print("***** RESULTS *****")
    #print(results)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)    
    return [(str(item.metadata['task'])) for item in sorted_results]

def get_davinci_response(prompt: str):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.7,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text.strip()

class Task:
    def __init__(self, id: int, name: str, objective = OBJECTIVE):
        self.id = id
        self.name = name
        self.objective = objective
        self.result = None
        if not self.name:
            raise ValueError("Task name cannot be empty")

    def print_self(self):
        print(self.to_string())

    def to_string(self):
        return f"{self.id}\t{self.name}\t{self.result}"
    
    def execute(self):
        if self.result: raise Exception(f"Tried to execute task \"{self.name}\", which has already been executed")
        context=context_agent(index=YOUR_TABLE_NAME, query=self.objective, n=5)
        self.result = get_davinci_response(f"You are an AI who performs one task based on the following objective: {self.objective}.\nTake into account these previously completed tasks: {context}\nYour task: {self.name}\nResponse:")

class TaskManager:
    def __init__(self):
        self.task_list = deque([])
        self.id_counter = 0
        self.add_task(YOUR_FIRST_TASK)
        self.objective = OBJECTIVE

    def add_task(self, task: str):
        # make sure that we're getting a string, print out what we have and the type if not
        if not isinstance(task, str):
            print("Task is not a string")
            print(task)
            print(type(task))
            exit()
        self.id_counter += 1 # TODO: should we be starting at 0 instead of 1?
        self.task_list.append(Task(self.id_counter, task))

    def print_tasks(self):
        for task in self.task_list: task.print_self()

    def create_tasks(self, result: Dict, task_description: str):
        prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {self.objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join([t.to_string() for t in self.task_list])}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
        # response = openai.Completion.create(engine="text-davinci-003",prompt=prompt,temperature=0.5,max_tokens=100,top_p=1,frequency_penalty=0,presence_penalty=0)
        new_tasks = get_davinci_response(prompt).split('\n')
        for t in new_tasks: self.add_task(t)

    def prioritize(self, this_task_id:int):
        task_names = [t.name for t in self.task_list]
        next_task_id = int(this_task_id)+1
        removal_string = "Remove any duplicate/extremely similar tasks." if REMOVE_SIMILAR_TASKS else "Do not remove any tasks."
        prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{OBJECTIVE}. {removal_string} Return the result as a numbered list, like:
        #. First task
        #. Second task
        Start the task list with number {next_task_id}."""
        # response = openai.Completion.create(engine="text-davinci-003",prompt=prompt,temperature=0.5,max_tokens=1000,top_p=1,frequency_penalty=0,presence_penalty=0)
        new_tasks = get_davinci_response(prompt).split('\n')
        self.task_list = deque()
        for task_string in new_tasks:
            if '.' in task_string:
                task_parts = task_string.split(".", 1)
            elif ':' in task_string:
                task_parts = task_string.split(":", 1)
            else:
                raise Exception(f"Task string {task_string} does not contain a period or colon. This functionality needs to be improved.")
            if len(task_parts) == 2:
                self.task_list.append(Task(task_parts[0].strip(), task_parts[1].strip()))


task_manager = TaskManager()

# Main loop
while True:
    if task_manager.task_list:
        # Print the task list
        print("\033[95m\033[1m"+"\n*****TASK LIST*****\n"+"\033[0m\033[0m")
        task_manager.print_tasks()

        # Step 1: Pull the first task
        task = task_manager.task_list.popleft()
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
        index.upsert([(result_id, get_ada_embedding(vector),{"task":task.name,"result":result})])

    # Step 3: Create new tasks and reprioritize task list
    task_manager.create_tasks(enriched_result, task.name)

    task_manager.prioritize(task.id)

time.sleep(1)  # Sleep before checking the task list again
