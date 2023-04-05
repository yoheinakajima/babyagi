import openai
import pinecone
import time
from agent_manager import AIAssistant
import yaml


# Load YAML configuration file
with open("configs/config.yaml", "r") as file:
    config = yaml.safe_load(file)

openai.api_key = config['openai']['api_key']
OBJECTIVE = config['project']["objective"]
pinecone.init(api_key=config['pinecone']['api_key'],
              environment=config['pinecone']['environment'])
table_name = 'test-table'
if table_name not in pinecone.list_indexes():
    pinecone.create_index(table_name, dimension=dimension,
                          metric=metric, pod_type=pod_type)

# Connect to the index
index = pinecone.Index(table_name)

# Initialize the AIAssistant with the configuration
ai_assistant = AIAssistant(config)

# Create a task manager and add the first task from the project configuration
# task_manager = ai_assistant.task_manager
# task_manager.add_task({"task_name": config["project"]["first_task"]})


def get_ada_embedding(text: str) -> List[float]:
    """
    Generate an ADA text embedding.

    :param text: Input text for embedding.
    :return: List of floats as ADA text embedding.
    """
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]


# Create a task manager and add the first task from the project configuration
task_manager = ai_assistant.task_manager

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
        print("\033[95m\033[1m"+"\n*****TASK LIST*****\n"+"\033[0m\033[0m")
        print(task_manager)

        # Step 1: Pull the first task
        task = task_manager.get_next_task()
        print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
        print(str(task['task_id'])+": "+task['task_name'])

        # Send to execution function to complete the task based on the context
        result = ai_assistant.execution_agent(OBJECTIVE, task["task_name"])
        this_task_id = int(task["task_id"])
        print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
        print(result)

        # Step 2: Enrich result and store in Pinecone
        # This is where you should enrich the result if needed
        enriched_result = {'data': result}
        result_id = f"result_{task['task_id']}"
        # extract the actual result from the dictionary
        vector = enriched_result['data']

        index.upsert([(result_id, get_ada_embedding(vector), {
                     "task": task['task_name'], "result":result})])

        # Step 3: Create new tasks and reprioritize task list
    new_tasks = ai_assistant.task_creation_agent(OBJECTIVE, result, task["task_name"], [
                                                 t["task_name"] for t in task_manager.task_list])

    for new_task in new_tasks:
        task_id_counter += 1
        new_task.update({"task_id": task_id_counter})
        task_manager.add_task(new_task)

    ai_assistant.prioritization_agent(this_task_id, OBJECTIVE)

time.sleep(1)  # Sleep before checking the task list again
