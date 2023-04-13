import requests
import time
from collections import deque
from typing import Dict, List
from sentence_transformers import SentenceTransformer
from langchain.vectorstores import FAISS
from langchain.embeddings.openai import OpenAIEmbeddings
# Update this to your Oobabooga Text Generation Web UI server's IP address.
# Follow the instructions here to set up the server:
# https://github.com/oobabooga/text-generation-webui
# Search Huggingface for vicuna13b-1.1 to find the model.
OOBA_SERVER = "localhost"

OBJECTIVE = "Solve world hunger"
INITIAL_TASK = "Develop a task list."

def generate_text(prompt):
    params = {
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
    }
    response = requests.post(f"http://{OOBA_SERVER}:7860/run/textgen", json=params).json()
    reply = response["data"][0]
    return reply

# Print OBJECTIVE
print("\033[96m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
print(OBJECTIVE)

# Create FAISS index
embeddings_model = OpenAIEmbeddings(model="text-embedding-ada-002")
index = FAISS.from_texts(["_"], embeddings_model, metadatas=[{"task":INITIAL_TASK}])

# Task list
task_list = deque([])
model = SentenceTransformer('sentence-transformers/LaBSE')

def add_task(task: Dict):
    task_list.append(task)

def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str]):
    prompt = (
        f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective}, "
        f"The last completed task has the result: {result}. This result was based on this task description: {task_description}. "
        f"These are incomplete tasks: {', '.join(task_list)}. "
        f"Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
    )
    new_tasks = generate_text(prompt).strip().split("\n")
    return [{"task_name": task_name} for task_name in new_tasks]

def prioritization_agent(this_task_id: int):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id) + 1
    prompt = (
        f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. """
        f"""Consider the ultimate objective of your team:{OBJECTIVE}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    )
    new_tasks = generate_text(prompt).strip().split("\n")
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})

def execution_agent(objective: str, task: str) -> str:
    context = context_agent(query=objective, n=5)
    prompt = (
        f"You are an AI who performs one task based on the following objective: {objective}.\n"
        f"Take into account these previously completed tasks: {context}\n"
        f"Your task: {task}\nResponse:"
    )
    return generate_text(prompt).strip()

def context_agent(query: str, index: str, n: int):
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
    new_tasks = task_creation_agent(OBJECTIVE, enriched_result, task["task_name"], [t["task_name"] for t in task_list])

    for new_task in new_tasks:
        task_id_counter += 1
        new_task.update({"task_id": task_id_counter})
        add_task(new_task)
    prioritization_agent(this_task_id)

    time.sleep(1)  # Sleep before checking the task list again
