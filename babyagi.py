import openai
import pinecone
import time
from collections import deque
from typing import Dict, List
import typer
import yaml
import os

app = typer.Typer()

##Load keys and variables
def load_variables():
    global YOUR_TABLE_NAME, agi_config, index, task_list

    agi_config = yaml.load(open('config.yaml'), Loader=yaml.CLoader)

    #Set API Keys
    OPENAI_API_KEY = os.getenv(agi_config["openai_api_key_var"])
    PINECONE_API_KEY = os.getenv(agi_config["pinecone_api_key_var"])
    PINECONE_ENVIRONMENT = agi_config["pinecone_env"] #Pinecone Environment (eg. "us-east1-gcp")

    #Set Variables
    YOUR_TABLE_NAME = agi_config["your_table_name"]

    # Configure OpenAI and Pinecone
    openai.api_key = OPENAI_API_KEY
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

    # Create Pinecone index
    table_name = YOUR_TABLE_NAME
    dimension = agi_config["pinecone_dimension"]
    metric = agi_config["pinecone_metric"]
    pod_type = agi_config["pinecone_pod_type"]
    if table_name not in pinecone.list_indexes():
        pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

    # Connect to the index
    index = pinecone.Index(table_name)

    # Task list
    task_list = deque([])

def add_task(task: Dict):
    task_list.append(task)

def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model=agi_config["ada_embedding_engine"])["data"][0]["embedding"]

def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str]):
    prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}. Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Return the tasks as an array."
    response = openai.Completion.create(
        engine=agi_config["openai_completion_engine"],
        prompt=prompt,
        temperature=agi_config["openai_creation_temperature"],
        max_tokens=agi_config["openai_creation_max_tokens"],
        top_p=agi_config["openai_top_p"],
        frequency_penalty=agi_config["openai_frequency_penalty"],
        presence_penalty=agi_config["openai_presence_penalty"]
        )
    new_tasks = response.choices[0].text.strip().split('\n')
    return [{"task_name": task_name} for task_name in new_tasks]

def prioritization_agent(this_task_id:int, objective:str):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id)+1
    prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{objective}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    response = openai.Completion.create(
        engine=agi_config["openai_completion_engine"],
        prompt=prompt,
        temperature=agi_config["openai_prioritization_temperature"],
        max_tokens=agi_config["openai_prioritization_max_tokens"],
        top_p=agi_config["openai_top_p"],
        frequency_penalty=agi_config["openai_frequency_penalty"],
        presence_penalty=agi_config["openai_presence_penalty"])
    new_tasks = response.choices[0].text.strip().split('\n')
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})

def execution_agent(objective:str,task: str) -> str:
    #context = context_agent(index="quickstart", query="my_search_query", n=5)
    context=context_agent(index=YOUR_TABLE_NAME, query=objective, n=5)
    #print("\n*******RELEVANT CONTEXT******\n")
    #print(context)
    response = openai.Completion.create(
        engine=agi_config["openai_completion_engine"],
        prompt=f"You are an AI who performs one task based on the following objective: {objective}. Your task: {task}\nResponse:",
        temperature=agi_config["openai_execution_temperature"],
        max_tokens=agi_config["openai_execution_max_tokens"],
        top_p=agi_config["openai_top_p"],
        frequency_penalty=agi_config["openai_frequency_penalty"],
        presence_penalty=agi_config["openai_presence_penalty"]
    )
    return response.choices[0].text.strip()

def context_agent(query: str, index: str, n: int):
    query_embedding = get_ada_embedding(query)
    index = pinecone.Index(index_name=index)
    results = index.query(query_embedding, top_k=n,
    include_metadata=True)
    #print("***** RESULTS *****")
    #print(results)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)    
    return [(str(item.metadata['task'])) for item in sorted_results]



@app.command()
def main(

    objective: str = typer.Argument(..., help="Your objective"),
    first_task: str = typer.Argument(..., help="Your first task"),
):
    load_variables()

    
    # Print OBJECTIVE
    print("\033[96m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
    print(objective)

    # Add the first task
    first_task = {
        "task_id": 1,
        "task_name": first_task
    }

    add_task(first_task)
    # Main loop
    task_id_counter = 1
    while True:
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
            result = execution_agent(objective,task["task_name"])
            this_task_id = int(task["task_id"])
            print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
            print(result)

            # Step 2: Enrich result and store in Pinecone
            enriched_result = {'data': result}  # This is where you should enrich the result if needed
            result_id = f"result_{task['task_id']}"
            vector = enriched_result['data']  # extract the actual result from the dictionary
            index.upsert([(result_id, get_ada_embedding(vector),{"task":task['task_name'],"result":result})])

        # Step 3: Create new tasks and reprioritize task list
        new_tasks = task_creation_agent(objective,enriched_result, task["task_name"], [t["task_name"] for t in task_list])

        for new_task in new_tasks:
            task_id_counter += 1
            new_task.update({"task_id": task_id_counter})
            add_task(new_task)
        prioritization_agent(this_task_id, objective)

        time.sleep(1)  # Sleep before checking the task list again

if __name__ == "__main__":
    typer.run(main())