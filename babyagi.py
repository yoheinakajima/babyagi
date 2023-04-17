import os
import time
from collections import deque
from typing import Dict, List
import importlib
import json
import openai
from colorama import Fore
import pinecone
from dotenv import load_dotenv

# import local modules
from local_memory import LocalMemory
from ai_responses import get_ada_embedding, openai_call
from task_agent import TaskAgent

# Load default environment variables (.env)
load_dotenv()

# Starting configuation
DEFAULT_BABY_NAME = os.getenv('BABY_NAME')
BABY_NAME = input(f"Give this toddler a name: (default: {DEFAULT_BABY_NAME}): ").strip()
if BABY_NAME=='':
    BABY_NAME==DEFAULT_BABY_NAME
DEFAULT_OBJECTIVE = os.getenv("OBJECTIVE", "")
OBJECTIVE = input(f"Give the AI an objective (default: {DEFAULT_OBJECTIVE}): ").strip()
if OBJECTIVE=='':
    OBJECTIVE=DEFAULT_OBJECTIVE

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
assert OPENAI_API_MODEL, "OPENAI_API_MODEL environment variable is missing from .env"

if "gpt-4" in OPENAI_API_MODEL.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
assert (
    PINECONE_ENVIRONMENT
), "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Table config
YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert YOUR_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

DEBUG_MODE = os.getenv("DEBUG_MODE")=='TRUE'
INITIAL_TASK = os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", ""))

if DEBUG_MODE:
    print(Fore.YELLOW + 'Using DEBUG mode, will show debugging output and pause at end of each loop.' + Fore.RESET)

# Model configuration
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.0))


# Extensions support begin

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


DOTENV_EXTENSIONS = os.getenv("DOTENV_EXTENSIONS", "").split(" ")

# Command line arguments extension
# Can override any of the above environment variables
ENABLE_COMMAND_LINE_ARGS = (
    os.getenv("ENABLE_COMMAND_LINE_ARGS", "false").lower() == "true"
)
if ENABLE_COMMAND_LINE_ARGS:
    if can_import("extensions.argparseext"):
        from extensions.argparseext import parse_arguments

        OBJECTIVE, INITIAL_TASK, OPENAI_API_MODEL, DOTENV_EXTENSIONS = parse_arguments()

# Load additional environment variables for enabled extensions
if DOTENV_EXTENSIONS:
    if can_import("extensions.dotenvext"):
        from extensions.dotenvext import load_dotenv_extensions

        load_dotenv_extensions(DOTENV_EXTENSIONS)

# TODO: There's still work to be done here to enable people to get
# defaults from dotenv extensions # but also provide command line
# arguments to override them

# Extensions support end

# Check if we know what we are doing
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env"
assert INITIAL_TASK, "INITIAL_TASK environment variable is missing from .env"

if "gpt-4" in OPENAI_API_MODEL.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )

# Print OBJECTIVE
print("\033[94m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
print(f"{OBJECTIVE}")

print("\033[93m\033[1m" + "\nInitial task:" + "\033[0m\033[0m" + f" {INITIAL_TASK}")

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = YOUR_TABLE_NAME
dimension = 1536
metric = "cosine"
pod_type = "p1"

try:
    if os.getenv('USE_MEMORY')=='local':
        raise Exception('Using local storage for memory...')
    if table_name not in pinecone.list_indexes():
        pinecone.create_index(
            table_name, dimension=dimension, metric=metric, pod_type=pod_type
        )

    # Connect to the index
    index = pinecone.Index(table_name)
except:
    print('Setting up local memory store. This is a test feature and may not produce the same results.')
    index = LocalMemory(BABY_NAME, resume=False)


# Identify/Create file for saving results
saved_results_folder = f'saved_results/{BABY_NAME}'
if not os.path.exists(saved_results_folder):
    os.mkdir(saved_results_folder)
else:
    for file in os.listdir(saved_results_folder):
        os.unlink(os.path.join(saved_results_folder, file))

# Task list
task_list = deque([])


def add_task(task: Dict):
    task_list.append(task)


def project_manager_agent(objective: str, finished_list, to_do_list: List[str], debug=False):
    prompt = f"""
    You are a project overseer AI that determins if the following objective has been successfully reached: {objective}
    Several AI execution agents have been working on tasks to complete the objective.
    Completed tasks: {', '.join(finished_list)}
    Incomplete tasks: {', '.join(to_do_list)}
    Respond with a JSON object that can be parsed by json.loads() and is structured:"""+"""'''
    {
        project_status: '<COMPLETE|IN_PROGRESS|IMPOSSIBLE>', 
        project_phase: '<PLANNING|EXECUTION|REVIEW>',
        incomplete_tasks: ['Do this thing', 'Do other thing'], 
        overseer_comment: '<brief comment>'
    }'''
    Do not include anything but the JSON object in your response.
    Response:"""
    if debug:
        print(f'Project Complete Agent Prompt:\n{prompt}')
    try:
        response_json = json.loads(openai_call(prompt, model=OPENAI_API_MODEL, temperature=OPENAI_TEMPERATURE))
    except json.decoder.JSONDecodeError:
        print("JSON parse failed! Trying again with more tokens allowed.")
        response_json = json.loads(openai_call(prompt, model=OPENAI_API_MODEL, temperature=OPENAI_TEMPERATURE, max_tokens=300))
    if debug:
        print(f'Project agent response:\n{response_json}')
    
    return response_json


def prioritization_agent(completed_tasks, incomplete_tasks, debug=False):
    global task_list
    prompt = f"""
    You are a task prioritization AI tasked with prioritizing the following list of tasks: {incomplete_tasks}.
    Consider the ultimate objective of your team:{OBJECTIVE}.
    Also consider the already-completed tasks: {completed_tasks}.
    Remove any duplicate tasks from the incomplete task list. Do not remove any other tasks or add new tasks.
    Return a JSON object of the prioritized incomplete tasks with the following format:"""+"""'''
    {
        prioritized_tasks: ['priority 1 task', 'priority 2 task']
    }'''
    Do not include anything but the JSON object in your response.
    Response:"""

    response = openai_call(prompt, model=OPENAI_API_MODEL, temperature=OPENAI_TEMPERATURE).strip()
    try:
        response_json = json.loads(response)
    except json.decoder.JSONDecodeError:
        print("JSON load fail! Trying again with more tokens")
        print(f"Received text: \n{response}")
        response_json = json.loads(openai_call(prompt, model=OPENAI_API_MODEL, temperature=OPENAI_TEMPERATURE, max_tokens=300).strip())
    
    new_tasks = response_json['prioritized_tasks']
    
    if debug:
        print(f'Prioritization Resopnse:\n{response_json}')

    
    return new_tasks


def context_agent(query: str, top_results_num: int):
    """
    Retrieves context for a given query from an index of tasks.

    Args:
        query (str): The query or objective for retrieving context.
        top_results_num (int): The number of top results to retrieve.

    Returns:
        list: A list of tasks as context for the given query, sorted by relevance.

    """
    query_embedding = get_ada_embedding(query)
    results = index.query(query_embedding, top_k=top_results_num, include_metadata=True, namespace=OBJECTIVE)
    # print("***** RESULTS *****")
    # print(results)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
    return [(str(item.metadata["task"])) for item in sorted_results]



completed_tasks = []

# Add the first task
first_task = {"task_id": 1, "task_name": INITIAL_TASK}

add_task(first_task)
# Main loop
task_id_counter = 0
mask_task_counter = 30
project_phase = 'PLANNING'
debugging = DEBUG_MODE
while True:
    task_id_counter += 1
    if task_id_counter == mask_task_counter:
        print("Task limit reached.")
        quit()
        
    if task_list:
        # Print the task list
        print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
        for t in task_list:
            print(str(t["task_id"]) + ": " + t["task_name"])

        # Step 1: Pull the first task from the list
        task = task_list.popleft()
        if task['task_name'].strip() == 'None':
            print(Fore.RED + "\n>>> No tasks remaining!\n" + Fore.RESET)
        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
        print(str(task["task_id"]) + ": " + task["task_name"])

        active_task = {
            "task_id": task['task_id'], 
            "task_name": task['task_name'], 
            "context":  context_agent(query=task["task_name"], top_results_num=5), 
            "feedback": None
        }  
        
        # Step 2: Spin up an execution agent and ask it to complete the given task
        execution_agent = TaskAgent(
            OBJECTIVE, task_name=active_task['task_name'], context=active_task['context'], debug=debugging)
        task_status = execution_agent.complete_task()
        active_task['result'] = execution_agent.result

        this_task_id = int(active_task["task_id"])
        print("\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
        print(active_task['result'])

        # Step 3: Save the results of the task
        completed_tasks.append(active_task)
        with open(os.path.join(saved_results_folder, f"{project_phase}.txt"), 'a') as f:
            f.write(
                f"""
Task: {active_task['task_id']}. {active_task['task_name']}
Result: {active_task['result']}
"""
                    )
        
        # step 4: Store the task in memory
        result_id = f"result_{task['task_id']}"
        vector = get_ada_embedding(
            active_task["result"]
        )  # get vector of the actual result extracted from the dictionary
        index.upsert(
            [(result_id, vector, {"task": active_task["task_name"], "result": active_task['result']})], 
            namespace=OBJECTIVE
        )
        
        completed_task_names = [str(x['task_id']) + '. ' + x['task_name'] for x in completed_tasks]
        to_do_task_names = [str(x['task_id']) + '. ' + x['task_name'] for x in task_list]

        # send list of completed/unfinished tasks to overseer for feedback
        if task_id_counter>1:
            overseer_feedback = project_manager_agent(
                OBJECTIVE, 
                completed_task_names, 
                to_do_task_names,
                debug=debugging
            )
            
            project_status = overseer_feedback['project_status']
            project_phase = overseer_feedback['project_phase']
            overseer_comment = overseer_feedback['overseer_comment']
            to_do_task_names = overseer_feedback['incomplete_tasks']
            if overseer_feedback['project_status'] == 'COMPLETE':
                print(Fore.LIGHTRED_EX + f'\n>>> Project status: COMPLETE\n>>> Comment: {overseer_comment}\n' + Fore.RESET)
                break
            else:
                print(Fore.LIGHTRED_EX + f'\n>>> Project status: {project_status}\n>>> Comment: {overseer_comment}\n' + Fore.RESET)
                if project_status=='IMPOSSIBLE':
                    break


        
        prioritized_tasks = prioritization_agent(completed_tasks, to_do_task_names, debugging)
        task_list = deque([])
        next_task_id = this_task_id 
        for to_do_task in prioritized_tasks:
            next_task_id += 1
            add_task({
                'task_id': next_task_id, 
                'task_name': to_do_task
            })
    
    if debugging:
        input('\n>>> DEBUG MODE: Press any key to continue ')
        print()

    time.sleep(1)  # Sleep before checking the task list again
