import openai
import pinecone
import os
import time
from collections import deque
from typing import Dict, List
from trello import TrelloClient

#Set API Keys
OPENAI_API_KEY = "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"
PINECONE_API_KEY = "26f5e5b3-1706-4c9d-8db4-6fd8e8a3886c"
PINECONE_ENVIRONMENT = "eu-west1-gcp" #Pinecone Environment (eg. "us-east1-gcp")
TRELLO_API_KEY = "3e54a834e284540111b618a2b4bc97b4"
TRELLO_API_TOKEN = "ATTA126ab749deaa1f0a316d0e53fef06c9c146c506696e4bb3a37b86721f057634eDC49CF0D"

# Set Variables
OBJECTIVE = "Create an automatic task completer, with GUI and Trello kanban board for tasks"
YOUR_FIRST_TASK = "Develop a task list."

# Print OBJECTIVE
print("\033[96m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
print(OBJECTIVE)

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = "taskevo"
dimension = 1024
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

# Connect to the index
index = pinecone.Index(table_name)

# Initialize Trello
trello_client = TrelloClient(
    api_key=TRELLO_API_KEY,
    api_secret=None,
    token=TRELLO_API_TOKEN,
    token_secret=None,
)


# Trello board and list creation
def create_trello_board(name: str):
    board = trello_client.add_board(name)
    return board


def create_trello_list(board, name: str):
    trello_list = board.add_list(name)
    return trello_list


board_name = "TaskEvo"
list_name = "Tasks"

trello_board = create_trello_board(board_name)
trello_list = create_trello_list(trello_board, list_name)
list_names = ["To Do", "In Progress", "Being Tested", "Human Review Needed", "Done", "Blocked"]

trello_lists = {}
for name in list_names:
    trello_lists[name] = create_trello_list(trello_board, name)


# Task list
task_list = deque([])


# Add task function
def add_task(task_id, task_data, task_status):
    index = pinecone.Index(table_name)
    task_vector = generate_vector(task_data)
    upsert_response = index.upsert(
        vectors=[(task_id, task_vector, {"status": task_status})],
    )
    index.deinit()

def find_similar_task(task_data):
    index = pinecone.Index(table_name)
    task_vector = generate_vector(task_data)
    query_response = index.query(
        top_k=1,
        include_values=True,
        include_metadata=True,
        vector=task_vector,
        filter={"status": {"$in": ["not_started"]}},
    )
    index.deinit()
    return query_response

def update_task_status(task_id, new_status):
    index = pinecone.Index(table_name)
    update_response = index.update(
        id=task_id,
        set_metadata={"status": new_status},
    )
    index.deinit()


# Get embeddings function
def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]


# Task creation agent function
def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str]):
    prompt = f"You are a task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective}. The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, temperature=0.5, max_tokens=100, top_p=1, frequency_penalty=0, presence_penalty=0)
    new_tasks = response.choices[0].text.strip().split('\n')
    return [{"task_name": task_name} for task_name in new_tasks]

# Prioritization agent function
def prioritization_agent(this_task_id:int):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id)+1
    prompt = f"""You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{OBJECTIVE}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    response = openai.Completion.create(engine="text-davinci-003", prompt=prompt, temperature=0.5, max_tokens=1000, top_p=1, frequency_penalty=0, presence_penalty=0)
    new_tasks = response.choices[0].text.strip().split('\n')
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})

# Execution agent function
def execution_agent(objective:str, task: str) -> str:
    context = context_agent(index=table_name, query=objective, n=5)
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=f"You are an AI who performs one task based on the following objective: {objective}. Your task: {task}\nResponse:",
        temperature=0.7,
        max_tokens=2000,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text.strip()

# Context agent function
def context_agent(query: str, index: str, n: int):
    query_embedding = get_ada_embedding(query)
    index = pinecone.Index(index_name=index)
    results = index.query(query_embedding, top_k=n,
    include_metadata=True)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)    
    return [(str(item.metadata['task'])) for item in sorted_results]

# Move card to list function
def move_card_to_list(card, list_name: str):
    target_list = trello_lists[list_name]
    card.change_list(target_list.id)

# Add the first task
task_id = "task1"
task_embedding = [0.1, 0.2, 0.3, 0.4]
task_metadata = {"status": "pending"}
#index.upsert(vectors=[(task_id, task_embedding, task_metadata)])

add_task(task_id, YOUR_FIRST_TASK, "pending")


# Main loop
task_id_counter = 1
attempt_counter = {}
max_attempts = 3

while True:
    cards = trello_lists["To Do"].list_cards()
    if cards:
        task = cards[0]
        task_id = task.id
        
        # Increment attempt counter for the task
        task_id = task["task_id"]
        if task_id in attempt_counter:
            attempt_counter[task_id] += 1
        else:
            attempt_counter[task_id] = 1

        # If the task has been attempted too many times, move it to "Human Review Needed" or "Blocked" list
        if attempt_counter[task_id] > max_attempts:
            move_card_to_list(task, "Human Review Needed")
            print(f"Task '{task['task_name']}' moved to 'Human Review Needed' list after {max_attempts} attempts.")
            continue

        # Print the task list
        print("\033[95m\033[1m"+"\n*****TASK LIST*****\n"+"\033[0m\033[0m")
        for t in task_list:
            print(str(t['task_id'])+": "+t['task_name'])

        # Step 1: Pull the first task and execute it
        task = cards[0]
        print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
        print(str(task['task_id'])+": "+task['task_name'])
        result = execution_agent(OBJECTIVE, task["task_name"])
        
        # Move the task to "Done" list
        move_card_to_list(task, "Done")
        this_task_id = int(task["task_id"])
        print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
        print(result)

        # Step 2: Enrich result and store in Pinecone
        enriched_result = {'data': result}
        result_id = f"result_{task['task_id']}"
        vector = enriched_result['data']
        index.upsert([(result_id, get_ada_embedding(vector), {"task": task['task_name'], "result": result})])

    # Step 3: Create new tasks and reprioritize task list
    new_tasks = task_creation_agent(OBJECTIVE, enriched_result, task["task_name"], [t["task_name"] for t in task_list])

    for new_task in new_tasks:
        task_id_counter += 1
        new_task.update({"task_id": task_id_counter})
        add_task(new_task)
    prioritization_agent(this_task_id)

time.sleep(1)  # Sleep before checking the task list again