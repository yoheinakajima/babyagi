import os
import requests
import time
from collections import deque
from typing import Dict, List
import importlib
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import FAISS
from dotenv import load_dotenv
load_dotenv()

# Server Configuration
## Update this to your Oobabooga Text Generation Web UI server's IP address.
## Follow the instructions here to set up the server:
## https://github.com/oobabooga/text-generation-webui
## Search Huggingface for vicuna13b-1.1 to find the model for your server.
OOBA_SERVER = os.getenv("OOBA_SERVER", "localhost")

# Goal configuation
OBJECTIVE = os.getenv("OBJECTIVE", "Solve world hunger")
INITIAL_TASK = os.getenv("INITIAL_TASK", "Develop a task list.")

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

def generate_text(prompt):
    response = requests.post(f"http://{OOBA_SERVER}:7860/run/textgen", json={
        'prompt': prompt,
        'max_new_tokens': 200,
        'temperature': 0.5,
        'top_p': 0.9,
        'typical_p': 1,
        'n': 1,
        'stop': None,
        'do_sample': True,
        'return_prompt': False,
        'return_metadata': False,
        'typical_p': 0.95,
        'repetition_penalty': 1.05,
        'encoder_repetition_penalty': 1.0,
        'top_k': 0,
        'min_length': 0,
        'no_repeat_ngram_size': 2,
        'num_beams': 1,
        'penalty_alpha': 0,
        'length_penalty': 1.0,
        'early_stopping': False,
        'pad_token_id': None,  # Padding token ID, if required
        'eos_token_id': None,  # End-of-sentence token ID, if required
        'use_cache': True,     # Whether to use caching
        'num_return_sequences': 1,  # Number of sequences to return for each input
        'bad_words_ids': None,  # List of token IDs that should not appear in the generated text
        'seed': -1,
    }).json()
    return response["data"][0]

# Check if we know what we are doing
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env"
assert INITIAL_TASK, "INITIAL_TASK environment variable is missing from .env"

# Print OBJECTIVE
print("\033[96m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
print(OBJECTIVE)

# Task list
task_list = deque([])
model = SentenceTransformer('sentence-transformers/LaBSE')

# Create FAISS index
def create_faiss_index(model, texts, metadatas):
    embeddings = model.encode(texts)
    index = FAISS(len(embeddings[0]))
    index.add(embeddings, metadatas)
    return index

index = create_faiss_index(model, [""], [{"task": INITIAL_TASK}])

def add_task(task: Dict):
    task_list.append(task)

def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str]):
    prompt = f"""
    You are a task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective},
    The last completed task has the result: {result}.
    This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}.
    Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks.
    Return the tasks as an array."""
    new_tasks = generate_text(prompt).strip().split("\n")
    return [{"task_name": task_name} for task_name in new_tasks]

def prioritization_agent(this_task_id: int):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id) + 1
    prompt = f"""
    You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}.
    Consider the ultimate objective of your team:{OBJECTIVE}.
    Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    new_tasks = generate_text(prompt).strip().split("\n")
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})

def execution_agent(objective: str, task: str) -> str:
    """
    Executes a task based on the given objective and previous context.

    Args:
        objective (str): The objective or goal for the AI to perform the task.
        task (str): The task to be executed by the AI.

    Returns:
        str: The response generated by the AI for the given task.

    """

    context = context_agent(query=objective, n=5)
    prompt = f"""
    You are an AI who performs one task based on the following objective: {objective}\n.
    Take into account these previously completed tasks: {context}\n.
    Your task: {task}\nResponse:"""
    return generate_text(prompt).strip()

def context_agent(query: str, index: str, n: int):
    """
    Retrieves context for a given query from an index of tasks.

    Args:
        query (str): The query or objective for retrieving context.
        n (int): The number of top results to retrieve.

    Returns:
        list: A list of tasks as context for the given query, sorted by relevance.

    """
    results = index.similarity_search_with_score(query, k=n)
    sorted_results = sorted(results, key=lambda x: x[1], reverse=True)
    return [item[0].metadata["task"] for item in sorted_results]

# Add the first task
first_task = {"task_id": 1, "task_name": INITIAL_TASK}

add_task(first_task)
# Main loop
task_id_counter = 1
while True:
    if task_list:
        # Print the task list
        print(
            "\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m"
        )
        for t in task_list:
            print(str(t["task_id"]) + ": " + t["task_name"])

        # Step 1: Pull the first task
        task = task_list.popleft()
        print(
            "\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m"
        )
        print(str(task["task_id"]) + ": " + task["task_name"])

        # Send to execution function to complete the task based on the context
        result = execution_agent(OBJECTIVE, task["task_name"])
        this_task_id = int(task["task_id"])
        print(
            "\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m"
        )
        print(result)

        # Step 2: Enrich result and store in index
        enriched_result = {"data": result}
        result_id = f'result_{task["task_id"]}'
        index.add_texts([result], metadatas=[{"task":task["task_name"]}])

    # Step 3: Create new tasks and reprioritize task list
    new_tasks = task_creation_agent(
        OBJECTIVE,
        enriched_result,
        task["task_name"],
        [t["task_name"] for t in task_list],
    )

    for new_task in new_tasks:
        task_id_counter += 1
        new_task.update({"task_id": task_id_counter})
        add_task(new_task)
    prioritization_agent(this_task_id)

    time.sleep(1)  # Sleep before checking the task list again
