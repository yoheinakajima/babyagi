import sys
import os
import openai
import pinecone
import yaml
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.task_manager import TaskManager
from src.utils import get_ada_embedding
from src.agents.context_agent import ContextAgent
from src.agents.execution_agent import ExecutionAgent
from src.agents.prioritization_agent import PrioritizationAgent
from src.agents.task_creation_agent import TaskCreationAgent


# Load YAML configuration file
with open("configs/config.yaml", "r", encoding="utf-8") as file:
    config = yaml.safe_load(file)

openai.api_key = config['openai']['api_key']
OBJECTIVE = config['project']["objective"]
TABLE_NAME = config['pinecone']['pinecone_index']['table_name']


pinecone.init(api_key=config['pinecone']['api_key'],
              environment=config['pinecone']['environment'])

if TABLE_NAME not in pinecone.list_indexes():
    pinecone.create_index(config['pinecone']['pinecone_index']['table_name'], dimension=config['pinecone']['dimension'],
                          metric=config['pinecone']['metric'], pod_type=config['pinecone']['pod_type'])

# Connect to the index
index = pinecone.Index(TABLE_NAME)

# Initialize individual agents
task_creation_agent = TaskCreationAgent(config["agents"]["task_creation"])
prioritization_agent = PrioritizationAgent(config["agents"]["prioritization"])

context_agent = ContextAgent(OBJECTIVE, TABLE_NAME, n=5)
execution_agent = ExecutionAgent(config["agents"]["execution"], context_agent)

# Create a task manager and add the first task from the project configuration
task_manager = TaskManager()

# Define your first task
first_task = {
    "task_id": 1,
    # Replace this with the actual task name
    "task_name": config["project"]["first_task"]
}

# Add the first task to the task manager
task_manager.add_task(first_task)

# Main loop
task_id_counter = 1
while True:
    if task_manager.has_tasks():
        # Print the task list
        print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
        print(task_manager)

        # Step 1: Pull the first task
        task = task_manager.get_next_task()
        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
        print(str(task['task_id']) + ": " + task['task_name'])

        # Send to execution function to complete the task based on the context
        result = execution_agent.execute_task(OBJECTIVE, task["task_name"])
        this_task_id = int(task["task_id"])
        print("\033[93m\033[1m" +
              "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
        print(result)

        # Step 2: Enrich result and store in Pinecone
        # This is where you should enrich the result if needed
        enriched_result = {'data': result}
        result_id = f"result_{task['task_id']}"
        # extract the actual result from the dictionary
        vector = enriched_result['data']



        index.upsert([(result_id, get_ada_embedding(vector), {
                     "task": task['task_name'], "result": result})])

        # Step 3: Create new tasks and reprioritize task list
    # new_tasks = task_creation_agent.create_tasks(OBJECTIVE, result, task["task_name"], [t["task_name"] for t in task_manager.task_list])
    new_tasks = task_creation_agent.create_tasks(OBJECTIVE, result, task["task_name"], task_manager)


    for new_task in new_tasks:
        task_id_counter += 1
        new_task.update({"task_id": task_id_counter})
        task_manager.add_task(new_task)

    prioritization_agent.prioritize_tasks(this_task_id, OBJECTIVE, task_manager)


time.sleep(1)  # Sleep before checking the task list again
