import openai
import pinecone
import time
import os
import threading
from collections import deque
from typing import Dict, List
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

#Set API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT")
PINECONE_TABLE = os.getenv("PINECONE_TABLE")

#Set OpenAI API Model
def choose_model():
    print("Please choose a model:")
    print("1. GPT-3 (text-davinci-003)")
    print("2. GPT-3.5")
    print("3. GPT-4 (Note: You must have GPT-4 API access to use this model.)")

    while True:
        choice = input("Enter the number corresponding to the model you want to use: ")
        
        if choice == '1':
            return "GPT-3"
        elif choice == '2':
            return "GPT-3.5"
        elif choice == '3':
            return "GPT-4"
        else:
            print("Invalid option. Please enter a valid number.")

#Set the "Model" variable using the input provided by the user
MODEL = choose_model()
print(f"Selected model: {MODEL}")

#Set Variables
OBJECTIVE = input("What is the objective of your AI system?: ")
YOUR_FIRST_TASK = input("What is the first task for your AI system?: ")

print("\033[93m\033[1m"+"\nNOTE: You can terminate the AI system at any time by typing 'kill' into the console.\n"+"\033[0m\033[0m")


#Print OBJECTIVE
print("\033[96m\033[1m"+"\n*****OBJECTIVE*****\n"+"\033[0m\033[0m")
print(OBJECTIVE)

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = PINECONE_TABLE
dimension = 1536
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

# Connect to the index
index = pinecone.Index(table_name)

# Task list
task_list = deque([])

def add_task(task: Dict):
    task_list.append(task)

def get_ada_embedding(text):
    text = [string.replace("\n", " ") for string in text]
    text = ''.join(text)
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str]):
    prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {OBJECTIVE}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
        # Model Selection
    if MODEL == 'GPT-3':
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        new_tasks = response.choices[0].text.strip().split('\n')
    elif MODEL == 'GPT-3.5':
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a task creation AI that uses the result of an execution agent to create new tasks with the objectives stated in the user content"},
                {"role": "user", "content": prompt},
            ]
        )
        new_tasks = response['choices'][0]['message']['content'].strip().split('\n')
    elif MODEL == 'GPT-4':
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a task creation AI that uses the result of an execution agent to create new tasks with the objectives stated in the user content"},
                {"role": "user", "content": prompt},
            ]
        )
        new_tasks = response['choices'][0]['message']['content'].strip().split('\n')
    return [{"task_name": task_name} for task_name in new_tasks]

def prioritization_agent(this_task_id:int):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id)+1
    prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{OBJECTIVE}. Do not remove any tasks. Return the result as a numbered list, like:
        #. First task
        #. Second task
        Start the task list with number {next_task_id}."""
        # Model Selection
    if MODEL == 'GPT-3':
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=100,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        new_tasks = response.choices[0].text.strip().split('\n')
    elif MODEL == 'GPT-3.5':
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks"},
                {"role": "user", "content": prompt},
            ]
        )
        new_tasks = response['choices'][0]['message']['content'].strip().split('\n')
    elif MODEL == 'GPT-4':
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks"},
                {"role": "user", "content": prompt},
            ]
        )
        new_tasks = response['choices'][0]['message']['content'].strip().split('\n')
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})

def execution_agent(objective:str,task: str) -> str:
    #context = context_agent(index="quickstart", query="my_search_query", n=5)
    context=context_agent(index=PINECONE_TABLE, query=objective, n=5)
    #print("\n*******RELEVANT CONTEXT******\n")
    #print(context)

    prompt=f"You are an AI who performs one task based on the following objective: {objective}.\nTake into account these previously completed tasks: {context}\nYour task: {task}\nResponse:"
    # Model Selection
    if MODEL == 'GPT-3':
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            temperature=0.5,
            max_tokens=1000,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].text.strip().split('\n')
    elif MODEL == 'GPT-3.5':
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI who performs one task based on the user objective."},
                {"role": "user", "content": prompt},
            ]
        )
        return response['choices'][0]['message']['content'].strip().split('\n')
    elif MODEL == 'GPT-4':
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an AI who performs one task based on the user objective."},
                {"role": "user", "content": prompt},
            ]
        )
        return response['choices'][0]['message']['content'].strip().split('\n')

def context_agent(query: str, index: str, n: int):
    query_embedding = get_ada_embedding(query)
    index = pinecone.Index(index_name=index)
    results = index.query(query_embedding, top_k=n,
    include_metadata=True)
    #print("***** RESULTS *****")
    #print(results)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)    
    return [(str(item.metadata['task'])) for item in sorted_results]

# Add the first task
first_task = {
    "task_id": 1,
    "task_name": YOUR_FIRST_TASK
}

add_task(first_task)
task_id_counter = 1

# Create a thread to listen for termination input
def termination_input(stop_event):
    while not stop_event.is_set():
        command = input("")
        if command.lower() == "kill":
            stop_event.set()
            print("Terminating the AI system...")

# Main loop
def main_loop(stop_event):
    global task_id_counter
    global task_list
    while not stop_event.is_set():  # while loop continues until stop_event is set
        if task_list:
            # Print the task list
            print("\033[95m\033[1m"+"\n*****TASK LIST*****\n"+"\033[0m\033[0m")
            for t in task_list:
                print(str(t['task_id'])+": "+t['task_name'])

            # Step 1: Pull the first task
            task = task_list.popleft()
            print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
            print(str(task['task_id'])+": "+task['task_name'])

            # Send to execution function to complete the task based on the context
            result = execution_agent(OBJECTIVE,task["task_name"])
            this_task_id = int(task["task_id"])
            print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
            print(' '.join(result))


            # Step 2: Enrich result and store in Pinecone
            enriched_result = {'data': result}  # This is where you should enrich the result if needed
            result_id = f"result_{task['task_id']}"
            vector = enriched_result['data']  # extract the actual result from the dictionary
            index.upsert([(result_id, get_ada_embedding(vector),{"task":task['task_name'],"result":result})])

        # Step 3: Create new tasks and reprioritize task list
        new_tasks = task_creation_agent(OBJECTIVE,enriched_result, task["task_name"], [t["task_name"] for t in task_list])

        for new_task in new_tasks:
            task_id_counter += 1
            new_task.update({"task_id": task_id_counter})
            add_task(new_task)
        prioritization_agent(this_task_id)

        time.sleep(1)  # Sleep before checking the task list again

# Initialize the stop_event
stop_event = threading.Event()

# Create and start the threads for the main loop and the termination input function
main_thread = threading.Thread(target=main_loop, args=(stop_event,))
input_thread = threading.Thread(target=termination_input, args=(stop_event,))

main_thread.start()
input_thread.start()

main_thread.join()
input_thread.join()