#!/usr/bin/env python3
import os
import time
import argparse
import importlib
import openai
import pinecone
from collections import deque
from typing import Dict, List
from dotenv import load_dotenv

#Set Variables
load_dotenv()

# Engine configuration

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Table config
YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert YOUR_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

# Run configuration

parser = argparse.ArgumentParser(
    add_help=False,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
cooperative mode enables multiple instances of babyagi to work towards the same objective.
 * none        - (default) no cooperation, each instance works on its own list of tasks
 * local       - local machine cooperation
                 uses ray to share the list of tasks for an objective
 * distributed - distributed cooperation (not implemented yet)
                 uses pinecone to share the list of tasks for an objective

examples:
 * start solving world hunger by creating initial list of tasks using GPT-4:
     %(prog)s -m local -t "Create initial list of tasks" -4 Solve world hunger
 * join the work on solving world hunger using GPT-3:
     %(prog)s -m local -j Solve world hunger
"""
)
parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
main objective description. Doesn\'t need to be quoted.
if not specified, get OBJECTIVE from environment.
''', default=[os.getenv("OBJECTIVE", "")])
parser.add_argument('-n', '--name', required=False, help='''
babyagi instance name.
if not specified, get BABY_NAME from environment.
''', default=os.getenv("BABY_NAME", "BabyAGI"))
parser.add_argument('-m', '--mode', choices=['n', 'none', 'l', 'local', 'd', 'distributed'], help='''
cooperative mode type
''', default='none')
group = parser.add_mutually_exclusive_group()
group.add_argument('-t', '--task', metavar='<initial task>', help='''
initial task description. must be quoted.
if not specified, get INITIAL_TASK from environment.
''', default=os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", "")))
group.add_argument('-j', '--join', action='store_true', help='''
join an existing objective.
install cooperative requirements.
''')
parser.add_argument('-4', '--gpt-4', dest='use_gpt4', action='store_true', help='''
use GPT-4 instead of GPT-3
''')
parser.add_argument('-h', '-?', '--help', action='help', help='''
show this help message and exit
''')

args = parser.parse_args()

BABY_NAME = args.name
if not BABY_NAME:
    print("\033[91m\033[1m"+"BabyAGI instance name missing\n"+"\033[0m\033[0m")
    parser.print_help()
    parser.exit()

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

module_name = "ray"
COOPERATIVE_MODE = args.mode
if COOPERATIVE_MODE in ['l', 'local'] and not can_import(module_name):
    print("\033[91m\033[1m"+f"Local cooperative mode requires package {module_name}\nInstall:  pip install -r requirements-cooperative.txt\n"+"\033[0m\033[0m")
    parser.print_help()
    parser.exit()
elif COOPERATIVE_MODE in ['d', 'distributed']:
    print("\033[91m\033[1m"+"Distributed cooperative mode is not implemented yet\n"+"\033[0m\033[0m")
    parser.print_help()
    parser.exit()

JOIN_EXISTING_OBJECTIVE = args.join
if JOIN_EXISTING_OBJECTIVE and COOPERATIVE_MODE in ['n', 'none']:
    print("\033[91m\033[1m"+f"Joining existing objective requires local or distributed cooperative mode\n"+"\033[0m\033[0m")
    parser.print_help()
    parser.exit()

USE_GPT4 = args.use_gpt4

OBJECTIVE = ' '.join(args.objective).strip()
if not OBJECTIVE:
    print("\033[91m\033[1m"+"No objective specified or found in environment.\n"+"\033[0m\033[0m")
    parser.print_help()
    parser.exit()

INITIAL_TASK = args.task
if not INITIAL_TASK and not JOIN_EXISTING_OBJECTIVE:
    print("\033[91m\033[1m"+"No initial task specified or found in environment.\n"+"\033[0m\033[0m")
    parser.print_help()
    parser.exit()

print("\033[95m\033[1m"+"\n*****CONFIGURATION*****\n"+"\033[0m\033[0m")
print(f"Name: {BABY_NAME}")
print(f"LLM : {'GPT-4' if USE_GPT4 else 'GPT-3'}")
print(f"Mode: {'none' if COOPERATIVE_MODE in ['n', 'none'] else 'local' if COOPERATIVE_MODE in ['l', 'local'] else 'distributed' if COOPERATIVE_MODE in ['d', 'distributed'] else 'undefined'}")

if USE_GPT4:
    print("\033[91m\033[1m"+"\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"+"\033[0m\033[0m")

print("\033[94m\033[1m"+"\n*****OBJECTIVE*****\n"+"\033[0m\033[0m")
print(f"{OBJECTIVE}")

if not JOIN_EXISTING_OBJECTIVE: print("\033[93m\033[1m"+"\nInitial task:"+"\033[0m\033[0m"+f" {INITIAL_TASK}")
else: print("\033[93m\033[1m"+f"\nJoining to help the objective"+"\033[0m\033[0m")

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

# Task storage supporting only a single instance of BabyAGI
class SingleTaskListStorage:
    def __init__(self):
        self.tasks = deque([])
        self.task_id_counter = 0

    def append(self, task: Dict):
        self.tasks.append(task)

    def replace(self, tasks: List[Dict]):
        self.tasks = deque(tasks)

    def popleft(self):
        return self.tasks.popleft()

    def is_empty(self):
        return False if self.tasks else True

    def next_task_id(self):
        self.task_id_counter += 1
        return self.task_id_counter

    def get_task_names(self):
        return [t["task_name"] for t in self.tasks]

# Initialize tasks storage
tasks_storage = SingleTaskListStorage()
if COOPERATIVE_MODE in ['l', 'local']:
    print("")
    from ray_storage import CooperativeTaskListStorage
    tasks_storage = CooperativeTaskListStorage(OBJECTIVE)
elif COOPERATIVE_MODE in ['d', 'distributed']:
    pass

# Get embedding for the text
def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

# Call the correct GPT model
def openai_call(prompt: str, use_gpt4: bool = False, temperature: float = 0.5, max_tokens: int = 100):
    if not use_gpt4:
        # GPT-3 DaVinci
        response = openai.Completion.create(
            engine='text-davinci-003',
            prompt=prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].text.strip()
    else:
        # GPT-4 chat
        messages=[{"role": "user", "content": prompt}]
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages = messages,
            temperature=temperature,
            max_tokens=max_tokens,
            n=1,
            stop=None,
        )
        return response.choices[0].message.content.strip()

# Create the follow up tasks based on the objective, the result of the last task, and the list of incomplete tasks
def task_creation_agent(objective: str, result: Dict, task_description: str, tasks: List[str]):
    prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(tasks)}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
    response = openai_call(prompt, USE_GPT4)
    new_tasks = response.split('\n')
    return [{"task_name": task_name} for task_name in new_tasks]

# Reprioritize the incomplete tasks
def prioritization_agent():
    global tasks_storage
    task_names = tasks_storage.get_task_names()    
    prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{OBJECTIVE}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {tasks_storage.next_task_id()}."""
    response = openai_call(prompt, USE_GPT4)
    new_tasks = response.split('\n')
    new_tasks_list = []
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            new_tasks_list.append({"task_id": task_id, "task_name": task_name})
    tasks_storage.replace(new_tasks_list)

# Execute a task based on the objective and five previous tasks 
def execution_agent(objective:str, task: str) -> str:
    #context = context_agent(index="quickstart", query="my_search_query", n=5)
    context=context_agent(index=YOUR_TABLE_NAME, query=objective, n=5)
    #print("\n*******RELEVANT CONTEXT******\n")
    #print(context)
    prompt =f"You are an AI who performs one task based on the following objective: {objective}.\nTake into account these previously completed tasks: {context}\nYour task: {task}\nResponse:"
    return openai_call(prompt, USE_GPT4, 0.7, 2000)

# Get the top n completed tasks for the objective
def context_agent(query: str, index: str, n: int):
    query_embedding = get_ada_embedding(query)
    index = pinecone.Index(index_name=index)
    results = index.query(query_embedding, top_k=n, include_metadata=True)
    #print("***** RESULTS *****")
    #print(results)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)    
    return [(str(item.metadata['task'])) for item in sorted_results]

# Add the initial task if starting new objective
if not JOIN_EXISTING_OBJECTIVE:
    initial_task = {
        "task_id": tasks_storage.next_task_id(),
        "task_name": INITIAL_TASK
    }
    tasks_storage.append(initial_task)

# Main loop
while True:
    # As long as there are tasks in the storage...
    if not tasks_storage.is_empty():
        # Print the task list
        print("\033[96m\033[1m"+"\n*****TASK LIST*****\n"+"\033[0m\033[0m")
        for t in tasks_storage.get_task_names():
            print(" • "+t)

        # Step 1: Pull the first incomplete task
        task = tasks_storage.popleft()
        print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
        print(task['task_name'])

        # Send to execution function to complete the task based on the context
        result = execution_agent(OBJECTIVE, task["task_name"])
        print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
        print(result)

        # Step 2: Enrich result and store in Pinecone
        enriched_result = {'data': result}  # This is where you should enrich the result if needed
        result_id = f"result_{task['task_id']}"
        vector = enriched_result['data']  # extract the actual result from the dictionary
        index.upsert([(result_id, get_ada_embedding(vector), {"task":task['task_name'], "result":result})])

        # Step 3: Create new tasks and reprioritize task list
        new_tasks = task_creation_agent(OBJECTIVE, enriched_result, task["task_name"], tasks_storage.get_task_names())
        for new_task in new_tasks:
            new_task.update({"task_id": tasks_storage.next_task_id()})
            tasks_storage.append(new_task)

        prioritization_agent()

    time.sleep(1)  # Sleep before checking the task list again
