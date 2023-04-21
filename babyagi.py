#!/usr/bin/env python3
import os
import time
import logging
from collections import deque
from typing import Dict, List
import importlib
import openai
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from config.config import Config
# Load config
config = Config()

# Extensions support begin
def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

# Command line arguments extension
if config.enable_command_line_args:
    if can_import("extensions.argparseext"):
        from extensions.argparseext import parse_arguments
        config.objective, config.initial_task, config.llm_model, config.dotenv_extensions, config.instance_name, config.cooperative_mode, config.join_existing_objective = parse_arguments()

# Human mode extension
# Gives human input to babyagi
if config.llm_model == "HUMAN":
    if can_import("extensions.human_mode"):
        from extensions.human_mode import user_input_await

# Human mode extension
# Gives human input to babyagi
if LLM_MODEL == "HUMAN":
    if can_import("extensions.human_mode"):
        from extensions.human_mode import user_input_await

# Load additional environment variables for enabled extensions
# TODO: This might override the following command line arguments as well:
#    OBJECTIVE, INITIAL_TASK, LLM_MODEL, INSTANCE_NAME, COOPERATIVE_MODE, JOIN_EXISTING_OBJECTIVE
if config.dotenv_extensions:
    if can_import("extensions.dotenvext"):
        from extensions.dotenvext import load_dotenv_extensions
        load_dotenv_extensions(config.dotenv_extensions)


# TODO: There's still work to be done here to enable people to get
# defaults from dotenv extensions, but also provide command line
# arguments to override them

# Extensions support end

print("\033[95m\033[1m"+"\n*****CONFIGURATION*****\n"+"\033[0m\033[0m")
print(f"Name  : {config.instance_name}")
print(f"Mode  : {'alone' if config.cooperative_mode in ['n', 'none'] else 'local' if config.cooperative_mode in ['l', 'local'] else 'distributed' if config.cooperative_mode in ['d', 'distributed'] else 'undefined'}")
print(f"LLM   : {config.llm_model}")

if "llama" in config.llm_model.lower():
    if can_import("llama_cpp"):
        from llama_cpp import Llama

        print(f"LLAMA : {config.llama_model_path}" + "\n")
        assert os.path.exists(config.llama_model_path), "\033[91m\033[1m" + f"Model can't be found." + "\033[0m\033[0m"

        CTX_MAX = 2048
        THREADS_NUM = 16
        llm = Llama(
            model_path=config.llama_model_path,
            n_ctx=CTX_MAX, n_threads=THREADS_NUM,
            use_mlock=True,
        )
        llm_embed = Llama(
            model_path=config.llama_model_path,
            n_ctx=CTX_MAX, n_threads=THREADS_NUM,
            embedding=True, use_mlock=True,
        )

        print(
            "\033[91m\033[1m"
            + "\n*****USING LLAMA.CPP. POTENTIALLY SLOW.*****"
            + "\033[0m\033[0m"
        )
    else:
        print(
            "\033[91m\033[1m"
            + "\nLlama LLM requires package llama-cpp. Falling back to GPT-3.5-turbo."
            + "\033[0m\033[0m"
        )
        config.llm_model = "gpt-3.5-turbo"

if "gpt-4" in config.llm_model.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )

if "human" in LLM_MODEL.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING HUMAN INPUT*****"
        + "\033[0m\033[0m"
    )

print("\033[94m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
print(f"{config.objective}")

if not config.join_existing_objective: print("\033[93m\033[1m" + "\nInitial task:" + "\033[0m\033[0m" + f" {config.initial_task}")
else: print("\033[93m\033[1m" + f"\nJoining to help the objective" + "\033[0m\033[0m")

# Configure OpenAI
openai.api_key = config.open_ai_key

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
        embedding_function = OpenAIEmbeddingFunction(api_key=config.open_ai_key)
        self.collection = chroma_client.get_or_create_collection(
            name=config.restuls_store_name,
            metadata={"hnsw:space": metric},
            embedding_function=embedding_function,
        )

    def add(self, task: Dict, result: Dict, result_id: int, vector: List):

        # Break the function if LLM_MODEL starts with "human" (case-insensitive)
        if config.llm_model.lower().startswith("human"):
            return
        # Continue with the rest of the function

        embeddings = [llm_embed.embed(item) for item in vector] if config.llm_model.startswith("llama") else None
        if (
            len(self.collection.get(ids=[result_id], include=[])["ids"]) > 0
        ):  # Check if the result already exists
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
        return [item["task"] for item in results["metadatas"][0]]

# Initialize results storage
results_storage = DefaultResultsStorage()
if config.pinecone_api_key:
    if can_import("extensions.pinecone_storage"):
        from extensions.pinecone_storage import PineconeResultsStorage
        results_storage = PineconeResultsStorage(config.open_ai_key, config.pinecone_api_key, config.pinecone_environment, config.llm_model, config.llama_model_path, config.restuls_store_name, config.objective)
        print("\nReplacing results storage: " + "\033[93m\033[1m" +  "Pinecone" + "\033[0m\033[0m")

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
if config.cooperative_mode in ['l', 'local']:
    if can_import("extensions.ray_tasks"):
        import sys
        from pathlib import Path
        sys.path.append(str(Path(__file__).resolve().parent))
        from extensions.ray_tasks import CooperativeTaskListStorage
        tasks_storage = CooperativeTaskListStorage(config.objective)
        print("\nReplacing tasks storage: " + "\033[93m\033[1m" +  "Ray" + "\033[0m\033[0m")
elif config.cooperative_mode in ['d', 'distributed']:
    pass


def openai_call(
    prompt: str,
    model: str = config.llm_model,
    temperature: float = config.openai_temperature,
    max_tokens: int = 100,
):
    while True:
        try:
            if model.lower().startswith("llama"):
                result = llm(prompt[:CTX_MAX], stop=["### Human"], echo=True, temperature=0.2)
                return result['choices'][0]['text'].strip()
            elif model.lower().startswith("human"):
                return user_input_await(prompt)
            elif not model.lower().startswith("gpt-"):
                # Use completion API
                response = openai.Completion.create(
                    engine=model,
                    prompt=prompt,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0,
                )
                return response.choices[0].text.strip()
            else:
                # Use chat completion API
                messages = [{"role": "system", "content": prompt}]
                response = openai.ChatCompletion.create(
                    model=model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    n=1,
                    stop=None,
                )
                return response.choices[0].message.content.strip()
        except openai.error.RateLimitError:
            print(
                "   *** The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.Timeout:
            print(
                "   *** OpenAI API timeout occured. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIError:
            print(
                "   *** OpenAI API error occured. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIConnectionError:
            print(
                "   *** OpenAI API connection error occured. Check your network settings, proxy configuration, SSL certificates, or firewall rules. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.InvalidRequestError:
            print(
                "   *** OpenAI API invalid request. Check the documentation for the specific API method you are calling and make sure you are sending valid and complete parameters. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.ServiceUnavailableError:
            print(
                "   *** OpenAI API service unavailable. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        else:
            break


def task_creation_agent(
    objective: str, result: Dict, task_description: str, task_list: List[str]
):
    prompt = f"""
    You are a task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective},
    The last completed task has the result: {result}.
    This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}.
    Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks.
    Return the tasks as an array."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    return [{"task_name": task_name} for task_name in new_tasks]


def prioritization_agent():
    task_names = tasks_storage.get_task_names()
    next_task_id = tasks_storage.next_task_id()
    prompt = f"""
    You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}.
    Consider the ultimate objective of your team:{config.objective}.
    Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    new_tasks_list = []
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            new_tasks_list.append({"task_id": task_id, "task_name": task_name})
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
    # print("\n*******RELEVANT CONTEXT******\n")
    # print(context)
    prompt = f"""
    You are an AI who performs one task based on the following objective: {objective}\n.
    Take into account these previously completed tasks: {context}\n.
    Your task: {task}\nResponse:"""
    return openai_call(prompt, max_tokens=2000)


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
    # print("***** RESULTS *****")
    # print(results)
    return results

# Add the initial task if starting new objective
if not config.join_existing_objective:
    initial_task = {
        "task_id": tasks_storage.next_task_id(),
        "task_name": config.initial_task
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
            result = execution_agent(config.objective, task["task_name"])
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
                config.objective,
                enriched_result,
                task["task_name"],
                tasks_storage.get_task_names(),
            )

            for new_task in new_tasks:
                new_task.update({"task_id": tasks_storage.next_task_id()})
                tasks_storage.append(new_task)

            if not config.join_existing_objective: prioritization_agent()

        # Sleep a bit before checking the task list again
        time.sleep(5) 

if __name__ == "__main__":
    main()
