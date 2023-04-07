#!/usr/bin/env python3
import os
import openai
import pinecone
import time
import sys
from collections import deque
from typing import Dict, List
from dotenv import load_dotenv
import re
from agents.agent_module import create_python_developer_agent, create_javascript_developer_agent, create_researcher_agent, create_css_developer_agent, create_custom_agent, prioritization_agent, create_new_agents, create_terminal_agent, prompt_generator
from helper import openai_call

#Set Variables
load_dotenv()

agents = {}

# Set API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env from .env"

# Use GPT-3 model
USE_GPT4 = False
if USE_GPT4:
    print("\033[91m\033[1m"+"\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"+"\033[0m\033[0m")

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Table config
YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert YOUR_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

# Shared Context
YOUR_SHARED_CONTEXT = os.getenv("SHARED_CONTEXT", "")
assert YOUR_SHARED_CONTEXT, "SHARED_CONTEXT environment variable is missing from .env"

# Project config
OBJECTIVE = sys.argv[1] if len(sys.argv) > 1 else os.getenv("OBJECTIVE", "")
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

# Create Pinecone shared context
shared_context_table_name = YOUR_SHARED_CONTEXT
if shared_context_table_name not in pinecone.list_indexes():
    pinecone.create_index(shared_context_table_name, dimension=dimension, metric=metric, pod_type=pod_type)

# Connect to the shared context index
shared_context_index = pinecone.Index(shared_context_table_name)

# Task list
task_list = deque([])

def add_task(task: Dict):
    task_list.append(task)

def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

def task_creation_agent(objective: str, result: Dict, task_description: str, task_list: List[str], gpt_version: str = 'gpt-3'):
    required_keywords = {
        "python": ["python"],
        "javascript": ["javascript"],
        "terminal": ["terminal"],
        "research": ["research", "study"],
    }
    keywords = []
    for agent_type, agent_keywords in required_keywords.items():
        keywords += agent_keywords
    keyword_str = ", ".join(keywords)
    
    prompt = f"You are an task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective}, The last completed task has the result: {result}. This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}. Based on the result and using the keywords {keyword_str}, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. Only use the keywords if nessesary. The keywords are there to help trigger certain functions, only use them if the task actually requires one of the keywords. Return the tasks as an array."
    
    response = openai_call(prompt, USE_GPT4)
    new_tasks = response.split('\n')
    return [{"task_name": task_name} for task_name in new_tasks]

def context_agent(query: str, index_name: str, n: int):
    query_embedding = get_ada_embedding(query)
    results = index.query(query_embedding, top_k=n,
    include_metadata=True)
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)    
    return [(str(item.metadata['task'])) for item in sorted_results]

# Add the first task
first_task = {
    "task_id": 1,
    "task_name": YOUR_FIRST_TASK
}

def main_agent(task: Dict):
    task_name = task["task_name"].lower()
    agent_key = None

    if "python" in task_name:
        agent_key = "PythonDeveloper"
        if agent_key not in agents:
            agents[agent_key] = create_python_developer_agent()
    elif "javascript" in task_name:
        agent_key = "JavaScriptDeveloper"
        if agent_key not in agents:
            agents[agent_key] = create_javascript_developer_agent()
    elif "terminal" in task_name:
        agent_key = "TerminalUser"
        if agent_key not in agents:
            agents[agent_key] = create_terminal_agent()
    elif "research" in task_name:
        agent_key = "Researcher"
        if agent_key not in agents:
            agents[agent_key] = create_researcher_agent()
    if agent_key is not None:
        agent = agents[agent_key]
    else:
        if agent_key not in agents:
            prompt = prompt_generator(task_name, shared_context=shared_context)
            agents[agent_key] = create_custom_agent(agent_key, "Custom", prompt=prompt)
        agent = agents[agent_key]

    # Agents share information through a shared context or a messaging system
    shared_context = get_shared_context(task_name)
    result = agent(task, shared_context)

    # Check if there are new agents to be created
    new_agents = create_new_agents(result)
    for new_agent in new_agents:
        if new_agent['name'] not in agents:
            agents[new_agent['name']] = create_custom_agent(new_agent['name'], new_agent['role'])

    return result

# Example function to get shared context
def get_shared_context(context_key: str):
    query_embedding = get_ada_embedding(context_key)
    results = shared_context_index.query(query_embedding, top_k=1, include_metadata=True)

    if results.matches:
        return results.matches[0].metadata["value"]
    else:
        return None 
    

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

        # Send to main_agent function to complete the task based on the context
        result = main_agent(task)

        # process_response(result, task)

        this_task_id = int(task["task_id"])
        print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
        print(result)

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
    prioritization_agent(this_task_id, task_list=task_list, OBJECTIVE=OBJECTIVE)

    time.sleep(1)  # Sleep before checking the task list again
