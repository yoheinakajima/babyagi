import os
import time
import logging
from collections import deque
from typing import Dict, List
import importlib
import chromadb
from dotenv import load_dotenv
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings
from llama_cpp import Llama


# Load default environment variables (.env)
load_dotenv()

# Engine configuration
LLM_MODEL = "GPT4All"

# Table config
RESULTS_STORE_NAME = os.getenv("RESULTS_STORE_NAME", os.getenv("TABLE_NAME", ""))
assert RESULTS_STORE_NAME, "\033[91m\033[1m" + "RESULTS_STORE_NAME environment variable is missing from .env" + "\033[0m\033[0m"

# Run configuration
INSTANCE_NAME = os.getenv("INSTANCE_NAME", os.getenv("BABY_NAME", "BabyAGI"))
COOPERATIVE_MODE = "none"
JOIN_EXISTING_OBJECTIVE = False

# Goal configuation
OBJECTIVE = os.getenv("OBJECTIVE", "")
INITIAL_TASK = os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", ""))

# Model configuration
TEMPERATURE = float(os.getenv("TEMPERATURE", 0.2))

VERBOSE = (os.getenv("VERBOSE", "false").lower() == "true")

# Extensions support begin

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

print("\033[95m\033[1m"+"\n*****CONFIGURATION*****\n"+"\033[0m\033[0m")
print(f"Name  : {INSTANCE_NAME}")
print(f"Mode  : {'alone' if COOPERATIVE_MODE in ['n', 'none'] else 'local' if COOPERATIVE_MODE in ['l', 'local'] else 'distributed' if COOPERATIVE_MODE in ['d', 'distributed'] else 'undefined'}")
print(f"LLM   : {LLM_MODEL}")

# Check if we know what we are doing
assert OBJECTIVE, "\033[91m\033[1m" + "OBJECTIVE environment variable is missing from .env" + "\033[0m\033[0m"
assert INITIAL_TASK, "\033[91m\033[1m" + "INITIAL_TASK environment variable is missing from .env" + "\033[0m\033[0m"

MODEL_PATH = os.getenv("MODEL_PATH", "models/gpt4all-lora-quantized-ggml.bin")
    
print(f"GPT4All : {MODEL_PATH}" + "\n")
assert os.path.exists(MODEL_PATH), "\033[91m\033[1m" + f"Model can't be found." + "\033[0m\033[0m"

#CTX_MAX = 2048
#CTX_MAX = 8192
CTX_MAX = 16384
#THREADS_NUM = 16
THREADS_NUM = 4
llm = Llama(
    model_path=MODEL_PATH,
    n_ctx=CTX_MAX, n_threads=THREADS_NUM,
    use_mlock=True,
    verbose=False,
)
llm_embed = Llama(
    model_path=MODEL_PATH,
    n_ctx=CTX_MAX, n_threads=THREADS_NUM,
    embedding=True, use_mlock=True,
    verbose=False,
)

print("\033[94m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
print(f"{OBJECTIVE}")

if not JOIN_EXISTING_OBJECTIVE: print("\033[93m\033[1m" + "\nInitial task:" + "\033[0m\033[0m" + f" {INITIAL_TASK}")
else: print("\033[93m\033[1m" + f"\nJoining to help the objective" + "\033[0m\033[0m")

class LlamaEmbeddingFunction(EmbeddingFunction):
    def __init__(self, model: Llama):
        self._model = model

    def __call__(self, texts: Documents) -> Embeddings:
        # replace newlines, which can negatively affect performance.
        texts = [t.replace("\n", " ") for t in texts]
        embeddings = [self._model.embed(item) for item in texts]
        return embeddings

# Results storage using local ChromaDB
class DefaultResultsStorage:
    def __init__(self):
        logging.getLogger('chromadb').setLevel(logging.ERROR)
        # Create Chroma collection
        chroma_persist_dir = "chroma"
        chroma_client = chromadb.Client(
            settings=chromadb.config.Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=chroma_persist_dir,
            )
        )

        metric = "cosine"
        embedding_function = LlamaEmbeddingFunction(model=llm_embed)
        self.collection = chroma_client.get_or_create_collection(
            name=RESULTS_STORE_NAME,
            metadata={"hnsw:space": metric},
            embedding_function=embedding_function,
        )

    def add(self, task: Dict, result: Dict, result_id: str, vector: List):        
        embeddings = llm_embed.embed(vector)        

        if (len(self.collection.get(ids=[result_id], include=[])["ids"]) > 0):  # Check if the result already exists
            self.collection.update(
                ids=result_id,
                embeddings=embeddings,
                documents=vector,
                metadatas={"task": task["task_name"], "result": result},
            )
        else:
            self.collection.add(
                ids=result_id,
                embeddings=embeddings,
                documents=vector,
                metadatas={"task": task["task_name"], "result": result},
            )

    def query(self, query: str, top_results_num: int) -> List[dict]:
        count: int = self.collection.count()
        if count == 0:
            return []
        results = self.collection.query(
            query_texts=query,
            n_results=min(top_results_num, count),
            include=["metadatas"]
        )
        #return [item["task"] for item in results["metadatas"][0]]
        tasks = []        
        count = len(results["ids"][0])
        for i in range(count):
            item = results["metadatas"][0][i]
            resultidstr = results["ids"][0][i]
            resultid = resultidstr[7:]
            id = int(resultid)

            task = {}
            task['task_name'] = item["task"]
            task['task_id'] = id
            tasks.append(task)            
        return tasks
   

# Initialize results storage
results_storage = DefaultResultsStorage()

# Task storage supporting only a single instance of BabyAGI
class SingleTaskListStorage:
    def __init__(self):
        self.tasks = deque([])
        self.task_id_counter = 0

    def append(self, task: Dict):
        self.tasks.append(task)

    def replace(self, tasks: List[Dict]):
        self.tasks = deque(tasks)

    def popleft(self):
        return self.tasks.popleft()

    def is_empty(self):
        return False if self.tasks else True

    def next_task_id(self):
        self.task_id_counter += 1
        return self.task_id_counter

    def get_task_names(self):
        return [t["task_name"] for t in self.tasks]


# Initialize tasks storage
tasks_storage = SingleTaskListStorage()

def gpt_call(prompt: str, temperature: float = TEMPERATURE, max_tokens: int = 256):    
    result = llm(prompt[:CTX_MAX], echo=True, temperature=temperature, max_tokens=max_tokens)
    return result['choices'][0]['text'][len(prompt):].strip()

def strip_numbered_list(nl: List[str]) -> List[str]:
    result_list = []
    filter_chars = ['#', '(', ')', '[', ']', '.', ':', ' ']

    for line in nl:
        line = line.strip()
        if len(line) > 0:
            parts = line.split(" ", 1)
            if len(parts) == 2:
                left_part = ''.join(x for x in parts[0] if not x in filter_chars)
                if left_part.isnumeric():
                    result_list.append(parts[1].strip())
                else:
                    result_list.append(line)
            else:
                result_list.append(line)

    # filter result_list
    result_list = [line for line in result_list if len(line) > 3]
    
    # remove duplicates
    result_list = list(set(result_list))
    return result_list

def fix_prompt(prompt: str) -> str:
    lines = prompt.split("\n") if "\n" in prompt else [prompt]    
    return "\n".join([line.strip() for line in lines])

def task_creation_agent(
    objective: str, result: Dict, task_description: str, task_list: List[str]
):    
    prompt = f"""
    Your objective: {objective}\n
    Take into account these previously completed tasks but don't repeat them: {task_list}.\n
    The last completed task has the result: {result["data"]}.\n
    Develop a task list based on the result.\n
    Response:"""

    prompt = fix_prompt(prompt)

    response = gpt_call(prompt)
    pos = response.find("1")
    if (pos > 0):
        response = response[pos - 1:]

    if response == '':
        print("\n*** Empty Response from task_creation_agent***")
        new_tasks_list = result["data"].split("\n") if len(result) > 0 else [response]
    else:
        new_tasks = response.split("\n") if "\n" in response else [response]
        new_tasks_list = strip_numbered_list(new_tasks)
        
    return [{"task_name": task_name} for task_name in (t for t in new_tasks_list if not t == '')]


def prioritization_agent():
    task_names = tasks_storage.get_task_names()
    next_task_id = tasks_storage.next_task_id()    

    prompt = f"""
    Please prioritize, summarize and consolidate the following tasks: {task_names}.\n
    Consider the ultimate objective: {OBJECTIVE}.\n
    Return the result as a numbered list.
    """

    prompt = fix_prompt(prompt)

    response = gpt_call(prompt)
    pos = response.find("1")
    if (pos > 0):
        response = response[pos - 1:]

    new_tasks = response.split("\n") if "\n" in response else [response]
    new_tasks = strip_numbered_list(new_tasks)
    new_tasks_list = []
    i = 0
    for task_string in new_tasks:        
        new_tasks_list.append({"task_id": i + next_task_id, "task_name": task_string})
        i += 1
    
    if len(new_tasks_list) > 0:
        tasks_storage.replace(new_tasks_list)


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

    context_list = [t['task_name'] for t in context if t['task_name'] != INITIAL_TASK]
    #context_list = [t['task_name'] for t in context]

    # remove duplicates
    context_list = list(set(context_list))    

    if VERBOSE and len(context_list) > 0:
        print("\n*******RELEVANT CONTEXT******\n")
        print(context_list)

    if task == INITIAL_TASK:
        prompt = f"""
        You are an AI who performs one task based on the following objective: {objective}.\n
        Your task: {task}\nResponse:"""
    else:
        prompt = f"""
        Your objective: {objective}.\n
        Take into account these previously completed tasks but don't repeat them: {context_list}.\n
        Your task: {task}\n
        Response:"""

    #Give an advice how to achieve your task!\n

    prompt = fix_prompt(prompt)

    result = gpt_call(prompt)
    pos = result.find("1")
    if (pos > 0):
        result = result[pos - 1:]
    return result


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
    results = results_storage.query(query=query, top_results_num=top_results_num)
    #print("\n***** RESULTS *****")
    #print(results)
    return results

# Add the initial task if starting new objective
if not JOIN_EXISTING_OBJECTIVE:
    initial_task = {
        "task_id": tasks_storage.next_task_id(),
        "task_name": INITIAL_TASK
    }
    tasks_storage.append(initial_task)

def main ():
    while True:
        # As long as there are tasks in the storage...
        if not tasks_storage.is_empty():
            # Print the task list
            print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m\033[0m")
            for t in tasks_storage.get_task_names():
                print(" • "+t)

            # Step 1: Pull the first incomplete task
            task = tasks_storage.popleft()
            print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m")
            print(task['task_name'])

            # Send to execution function to complete the task based on the context
            result = execution_agent(OBJECTIVE, task["task_name"])            

            print("\033[93m\033[1m" + "\n*****TASK RESULT*****\n" + "\033[0m\033[0m")
            print(result)

            # Step 2: Enrich result and store in the results storage
            # This is where you should enrich the result if needed
            enriched_result = {
                "data": result
            }  
            # extract the actual result from the dictionary
            # since we don't do enrichment currently
            vector = enriched_result["data"]  

            result_id = f"result_{task['task_id']}"
            results_storage.add(task, result, result_id, vector)

            # Step 3: Create new tasks and reprioritize task list
            # only the main instance in cooperative mode does that
            new_tasks = task_creation_agent(
                OBJECTIVE,
                enriched_result,
                task["task_name"],
                tasks_storage.get_task_names(),
            )

            for new_task in new_tasks:
                if not new_task['task_name'] == '':
                    new_task.update({"task_id": tasks_storage.next_task_id()})
                    tasks_storage.append(new_task)

            if not JOIN_EXISTING_OBJECTIVE: prioritization_agent()

            # Sleep a bit before checking the task list again
            time.sleep(5) 

        else:
            print ("Ready, no more tasks.")

if __name__ == "__main__":
    main()
