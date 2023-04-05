import yaml
import openai
import pinecone
import time
from collections import deque
from typing import Dict, List
from agent_manager import AIAssistant
from task_manager import TaskManager

# Load YAML configuration
with open("configs/config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Initialize agents and task manager
pinecone_config = config["pinecone"]
openai_config = config["openai"]
project_config = config["project"]
agents_config = config["agents"]

pinecone.init(api_key=pinecone_config["api_key"], environment=pinecone_config["environment"])
openai.api_key = openai_config["api_key"]

assistant = AIAssistant(agents_config)
# task_manager = TaskManager()

# YOUR_FIRST_TASK = project_config["first_task"]
# OBJECTIVE = project_config["objective"]

# # Create Pinecone index
# pinecone_table_config = pinecone_config["pinecone_index"]
# table_name = pinecone_table_config["table_name"]
# dimension = pinecone_table_config["dimension"]
# metric = pinecone_table_config["metric"]
# pod_type = pinecone_table_config["pod_type"]

# if table_name not in pinecone.list_indexes():
#     pinecone.create_index(table_name, dimension=dimension, metric=metric, pod_type=pod_type)

# # Connect to the index
# index = pinecone.Index(table_name)

# # Add the first task
# first_task = {
#     "task_id": 1,
#     "task_name": YOUR_FIRST_TASK
# }

# task_manager.add_task(first_task)

# # Main loop
# task_id_counter = 1
# while True:
#     if task_manager.has_tasks():
#         # Print the task list
#         task_manager.print_task_list()

#         # Step 1: Pull the first task
#         task = task_manager.get_next_task()
#         print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
#         print(str(task['task_id']) + ": " + task['task_name'])

#         # Send to execution function to complete the task based on the context
#         result = assistant.execute("execution", {"objective": OBJECTIVE, "task": task["task_name"]})
#         this_task_id = int(task["task_id"])
#         print("\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
#         print(result)

    #     # Step 2: Enrich result and store in Pinecone
    #     enriched_result = {'data': result}
    #     result_id = f"result_{task['task_id']}"
    #     vector = enriched_result['data']
    #     index.upsert([(result_id, get_ada_embedding(vector), {"task": task['task_name'], "result": result})])

    #     # Step 3: Create new tasks and reprioritize task list
    #     new_tasks = assistant.create("task_creation", {"objective": OBJECTIVE, "result": enriched_result, "task_description": task["task_name"], "task_list": task_manager.get_task_names()})
    #     for new_task in new_tasks:
    #         task_id_counter += 1
    #         new_task.update({"task_id": task_id_counter})
    #         task_manager.add_task(new_task)

    #     task_manager.prioritize(assistant, OBJECTIVE, this_task_id)

    # time.sleep(1)  # Sleep before checking the task list again