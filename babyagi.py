#!/usr/bin/env python3
import os
import subprocess
import time
from collections import deque
from typing import Dict, List
import importlib
import openai
import pinecone
from dotenv import load_dotenv

import datetime

# Load default environment variables (.env)
load_dotenv()

# Engine configuration

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

# Goal configuation
OBJECTIVE = os.getenv("OBJECTIVE", "")
STOP_CRITERIA = os.getenv("STOP_CRITERIA", "")
PLAUSI_NUMBER = os.getenv("PLAUSI_NUMBER", "")
FINAL_PROMPT = os.getenv("FINAL_PROMPT", "")
INITIAL_TASK = os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", ""))

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

# Write output to file
def write_to_file(text: str, mode: chr):
    with open('task_list.txt', mode) as f:
        f.write(text)


# Print and write to file OBJECTIVE, STOP_CRITERIA and INITIAL_TASK
write_to_file(f"*****OBJECTIVE*****\n{OBJECTIVE}\n\n*****STOP CRITERIA*****\n{STOP_CRITERIA}\n\nInitial task: {INITIAL_TASK}\n\n", 'w')
print(f"\033[94m\033[1m\n*****OBJECTIVE*****\n\033[0m\033[0m{OBJECTIVE}")
print(f"\033[91m\033[1m\n*****STOP CRITERIA*****\n\033[0m\033[0m{STOP_CRITERIA}")
print(f"Initial task:\033[0m\033[0m {INITIAL_TASK}")

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = YOUR_TABLE_NAME
dimension = 1536
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    pinecone.create_index(
        table_name, dimension=dimension, metric=metric, pod_type=pod_type
    )

# Connect to the index
index = pinecone.Index(table_name)

# Task list
task_list = deque([])


def add_task(task: Dict):
    task_list.append(task)


def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]


def openai_call(
    prompt: str,
    model: str = OPENAI_API_MODEL,
    temperature: float = OPENAI_TEMPERATURE,
    max_tokens: int = 100,
):
    while True:
        try:
            if model.startswith("llama"):
                # Spawn a subprocess to run llama.cpp
                cmd = ["llama/main", "-p", prompt]
                result = subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True)
                return result.stdout.strip()
            elif not model.startswith("gpt-"):
                # Use completion API
                response = openai.Completion.create(
                    engine=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response.choices[0].text.strip()
            else:
                # Use chat completion API
                messages = [{"role": "system", "content": prompt}]
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    n=1,
                    stop=None,
                )
                return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            print(
                "   *** The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.Timeout:
            print(
                "   *** OpenAI API timeout occured. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIError:
            print(
                "   *** OpenAI API error occured. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIConnectionError:
            print(
                "   *** OpenAI API connection error occured. Check your network settings, proxy configuration, SSL certificates, or firewall rules. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.InvalidRequestError:
            print(
                "   *** OpenAI API invalid request. Check the documentation for the specific API method you are calling and make sure you are sending valid and complete parameters. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.ServiceUnavailableError:
            print(
                "   *** OpenAI API service unavailable. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        else:
            break


# Create new tasks with reasoning for stop criteria and calculation of last task's result contribution to objective
def task_creation_agent(
    objective: str, result: Dict, task_description: str, task_list: List[str]
):
    prompt = f"""
    You are a task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective},
    The last completed task has the result: {result}.
    This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}.\n
    Do only create new tasks which do directly contribute to the ultimate objective. The ultimate objective is: {OBJECTIVE}.\n
    Consider the stop criteria regarding the achievement of the ultimate objective. When it is met, and only then, create one new task with only content 'Stop criteria has been met...'.
    Here is the stop criteria: {STOP_CRITERIA}.\n
    Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks.
    Your aim is to create as few new tasks as possible to achieve the objective, with focus on the ultimate objective.
    Return the tasks as an array.\n\n
    Also evaluate the last completed task result regarding the contribution to the ultimate objective, and output 'Goal achievement [%]: ' followed by a number between 0 and 100.
    0 means we are very far away from the ultimate objective and 100 means the ulitmate objective has been achieved.
    Always do your best to determine an exact number. If there is any contribution at all, assign a number greater than 0.
    If the goal achievement output value cannot be determined, output 'Goal achievement [%]: unclear' and do only set it to 100, if the stop criteria has been met.
    Output the goal achievement in one line, and only one line. Output the goal achievement at the end with one empty line before.\n
    If the goal achievement value is 0 create new tasks for a different important open topic regarding the ultimate objective than in the last completed task result."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]

    # Remove the goal achievement from new tasks
    for n in new_tasks:
        if "Goal achievement [%]:" in n:
            new_tasks.remove(n)
            break

    # Get the goal achievement probability
    line = response.split("\n")
    probability = -1
    for l in line:
        if "Goal achievement" in l:
            try:
                probability = int(l.split(": ")[1])
                break
            except (ValueError, IndexError):
                probability = -1
    #print(f"\nProbability: {probability}%")
    return [{"task_name": task_name} for task_name in new_tasks], probability


# Prioritize the task list
def prioritization_agent(this_task_id: int):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id) + 1
    prompt = f"""
    You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}.\n
    Consider the ultimate objective of your team of agent functions: {OBJECTIVE}.\n
    Your aim is to prioritize the task list in a way that the ultimate objective is achieved with as few tasks as possible, and that the most relevant tasks are completed first.
    When continueing research on a particular category of the ultimate objective, consider the ultimate objective as a whole and switch to another category if necessary.
    Consider the order of the task list, with respect to which task depends on which and the order of creation, and improve the task list prioritization process.\n
    Do not remove any tasks. Return the result as a numbered list, like:
    1. Description of first task
    2. Description of second task
    3. Description of third task
    4. ...
    Start the task list with number {next_task_id}."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})


# Execute a task based on the objective and five previous tasks 
def execution_agent(objective: str, task: str) -> str:
    """
    Executes a task based on the given objective and previous context.

    Args:
        objective (str): The objective or goal for the AI to perform the task.
        task (str): The task to be executed by the AI.

    Returns:
        str: The response generated by the AI for the given task.

    """
    context = context_agent(query=objective, top_results_num=5)
    print(f"\033[96m\033[1m\n*****RELEVANT CONTEXT*****\033[0m\033[0m{context}")
    write_to_file(f"*****RELEVANT CONTEXT*****\n{context}\n", 'a')
    prompt = f"""
    You are an AI who performs one task based on the following objective: {objective}.\n
    Take into account these previously completed tasks: {context}.\n
    The one performed task must contribute to the achievement of the ultimate objective: {OBJECTIVE}.\n
    Your task: {task}\nResponse:"""
    return openai_call(prompt, max_tokens=2000)


# Get the top n completed tasks for the objective
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
    #print(f"\033[96m\033[1m\n*****CONTEXT QUERY*****\n\033[0m\033[0m{results}")
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
    return [(str(item.metadata["task"])) for item in sorted_results]


# Send final prompt and handle final response(s)
def final_prompt():
    response = openai_call(f"{FINAL_PROMPT}. The ultimate objective is: {OBJECTIVE}.")
    write_to_file(f"*****FINAL RESPONSE*****\n{response}\n", 'a')
    print(f"\033[94m\033[1m\n*****FINAL RESPONSE*****\n\033[0m\033[0m{response}")
    while "The final response generation has been completed" not in response:
        response = openai_call("Continue with output. Say 'The final response generation has been completed...' in case the complete result has been output already or the prompt is unclear.")
        write_to_file(f"{response}", 'a')
        print(response)
    print("\n***** The ultimate objective has been achieved, the work is done! BabyAGI will take a nap now... :-) *****\n")


# Add the first task
first_task = {"task_id": 1, "task_name": INITIAL_TASK}
add_task(first_task)
# Main loop
task_id_counter = 1
task_contribution = 0     # Percentage of goal achievement
plausi_counter = 0.0    # Counter for number of plausibility checks for goal achievement
while True:
    if task_list:
        # Print the task list
        print("\033[95m\033[1m" + "\n*****TASK LIST*****" + "\033[0m\033[0m")
        write_to_file("*****TASK LIST*****\n", 'a')
        for t in task_list:
            print(str(t["task_id"]) + ": " + t["task_name"])
            write_to_file(str(t["task_id"]) + ": " + t["task_name"] + "\n\n", 'a')

        # Step 1: Pull the first task
        task = task_list.popleft()

        # Check for stop criteria text in task name or (optional) plausi counter overflow
        if "Stop criteria has been met" in task["task_name"] or (plausi_counter >= float(PLAUSI_NUMBER) and float(PLAUSI_NUMBER) > 0):
            final_prompt()
            break

        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m" + str(task["task_id"]) + ": " + task["task_name"])
        write_to_file("*****NEXT TASK*****\n" + str(task["task_id"]) + ": " + task["task_name"] + "\n\n", 'a')

        # Send to execution function to complete the task based on the context
        result = execution_agent(OBJECTIVE, task["task_name"])
        this_task_id = int(task["task_id"])
        print(f"\033[93m\033[1m\n*****TASK RESULT*****\n\033[0m\033[0m{result}")
        write_to_file(f"\n*****TASK RESULT*****\n{result}\n", 'a')

        # Step 2: Enrich result with metadata and store in Pinecone
        enriched_result = {
            "data": result
        }  # This is where you should enrich the result if needed
        result_id = f"result_{task['task_id']}"
        vector = get_ada_embedding(
            enriched_result["data"]
        )  # get vector of the actual result extracted from the dictionary
        index.upsert(
            [(result_id, vector, {"task": task["task_name"], "result": result})],
	        namespace=OBJECTIVE
        )

        # Step 3: Create new tasks and reprioritize task list
        new_tasks, task_contribution = task_creation_agent(
            OBJECTIVE,
            enriched_result,
            task["task_name"],
            [t["task_name"] for t in task_list],
        )

        # Check for goal achievement contribution and increment plausi counter
        if task_id_counter > 3 and task_contribution > 0 and task_contribution <= 100:
                plausi_counter += (task_contribution*0.01)

        print(f"\033[94m\033[1m\n*****TASK GOAL ACHIEVEMENT*****\033[0m\033[0m")
        print(f"Plausi counter: {plausi_counter} with threshold: {PLAUSI_NUMBER} and contribution to objective: {task_contribution}%")  
        write_to_file(f"\n*****TASK GOAL ACHIEVEMENT*****\n", 'a')
        write_to_file(f"Plausi counter: {plausi_counter} with threshold: {PLAUSI_NUMBER} and contribution to objective: {task_contribution}%\n\n", 'a')

        for new_task in new_tasks:
            task_id_counter += 1
            new_task.update({"task_id": task_id_counter})
            add_task(new_task)
        prioritization_agent(this_task_id)

    time.sleep(1)  # Sleep before checking the task list again

