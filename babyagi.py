#!/usr/bin/env python3
import os
import subprocess
import time
from collections import deque
from typing import Dict, List
import importlib
import openai
import pinecone
from dotenv import load_dotenv

from extensions.google_search import get_toplist


# Load default environment variables (.env)
load_dotenv()

# Engine configuration

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

OPENAI_API_MODEL = os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")
assert OPENAI_API_MODEL, "OPENAI_API_MODEL environment variable is missing from .env"

if "gpt-4" in OPENAI_API_MODEL.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")
assert (
    PINECONE_ENVIRONMENT
), "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Table config
YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert YOUR_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

# Goal configuation
OBJECTIVE = os.getenv("OBJECTIVE", "")
STOP_CRITERIA = os.getenv("STOP_CRITERIA", "")
PLAUSI_NUMBER = os.getenv("PLAUSI_NUMBER", "")
CONTRIBUTION_THRESHOLD  = os.getenv("CONTRIBUTION_THRESHOLD", "")
FINAL_PROMPT = os.getenv("FINAL_PROMPT", "")
INITIAL_TASK = os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", ""))

# Model configuration
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.0))

# Google API configuration
YOUR_GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")
YOUR_SEARCH_ENGINE_ID = os.getenv("SEARCH_ENGINE_ID", "")


# Extensions support begin

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


DOTENV_EXTENSIONS = os.getenv("DOTENV_EXTENSIONS", "").split(" ")

# Command line arguments extension
# Can override any of the above environment variables
ENABLE_COMMAND_LINE_ARGS = (
    os.getenv("ENABLE_COMMAND_LINE_ARGS", "false").lower() == "true"
)
if ENABLE_COMMAND_LINE_ARGS:
    if can_import("extensions.argparseext"):
        from extensions.argparseext import parse_arguments

        OBJECTIVE, INITIAL_TASK, OPENAI_API_MODEL, DOTENV_EXTENSIONS = parse_arguments()

# Load additional environment variables for enabled extensions
if DOTENV_EXTENSIONS:
    if can_import("extensions.dotenvext"):
        from extensions.dotenvext import load_dotenv_extensions

        load_dotenv_extensions(DOTENV_EXTENSIONS)

# TODO: There's still work to be done here to enable people to get
# defaults from dotenv extensions # but also provide command line
# arguments to override them

# Extensions support end

# Check if we know what we are doing
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env"
assert INITIAL_TASK, "INITIAL_TASK environment variable is missing from .env"

if "gpt-4" in OPENAI_API_MODEL.lower():
    print(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )


# Write output to file
def write_to_file(text: str, mode: chr):
    with open('task_list.txt', mode) as f:
        f.write(text)


# Print and write to file OBJECTIVE, STOP_CRITERIA and INITIAL_TASK
write_to_file(f"*****OBJECTIVE*****\n{OBJECTIVE}\n\n*****STOP CRITERIA*****\n{STOP_CRITERIA}\n\nInitial task: {INITIAL_TASK}\n\n", 'w')
print(f"\033[94m\033[1m\n*****OBJECTIVE*****\n\033[0m\033[0m{OBJECTIVE}")
print(f"\033[91m\033[1m\n*****STOP CRITERIA*****\n\033[0m\033[0m{STOP_CRITERIA}")
print(f"\033[93m\033[1m\nInitial task:\033[0m\033[0m {INITIAL_TASK}")

# Configure OpenAI and Pinecone
openai.api_key = OPENAI_API_KEY
pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)

# Create Pinecone index
table_name = YOUR_TABLE_NAME
dimension = 1536
metric = "cosine"
pod_type = "p1"
if table_name not in pinecone.list_indexes():
    pinecone.create_index(
        table_name, dimension=dimension, metric=metric, pod_type=pod_type
    )

# Connect to the index
index = pinecone.Index(table_name)

# Task list
task_list = deque([])


def add_task(task: Dict):
    task_list.append(task)


def get_ada_embedding(text):
    text = text.replace("\n", " ")
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")[
        "data"
    ][0]["embedding"]


def openai_call(
    prompt: str,
    model: str = OPENAI_API_MODEL,
    temperature: float = OPENAI_TEMPERATURE,
    max_tokens: int = 100,
):
    while True:
        try:
            if model.startswith("llama"):
                # Spawn a subprocess to run llama.cpp
                cmd = ["llama/main", "-p", prompt]
                result = subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL, stdout=subprocess.PIPE, text=True)
                return result.stdout.strip()
            elif not model.startswith("gpt-"):
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


# Create new tasks with reasoning for stop criteria and calculation of last task's result contribution to objective
def task_creation_agent(
    objective: str, result: Dict, task_description: str, task_list: List[str], threshold: int
):
    prompt = f"""
    You are a task creation AI that uses the result of an execution agent to create new tasks with the following objective: {objective},
    The last completed task has the result: {result}
    This result was based on this task description: {task_description}. These are incomplete tasks: {', '.join(task_list)}\n
    Do only create new tasks which contribute to the ultimate objective. This is the ultimate objective: {OBJECTIVE}\n
    Take into account the stop criteria. When it is met, and only then, create one new task with only content 'Stop criteria has been met...'. 
    Here is the stop criteria: {STOP_CRITERIA}\n
    Based on the result, create new tasks to be completed by the AI system that do not overlap with incomplete tasks. 
    Your aim is to create as few new tasks as possible to achieve the objective, while keeping focus on the objective. 
    Do make sure that new tasks are properly verbalized and optimized for prompting a large language model. 
    If {YOUR_GOOGLE_API_KEY} is {""} or {YOUR_SEARCH_ENGINE_ID} is {""}, internet search is not possible. This must be considered for creation of new tasks, no new tasks including, refering to or dealing with internet search shall be created.
    Return the tasks as an array.\n\n
    Also evaluate the last completed task result regarding the contribution to the ultimate objective, and output 'Contribution [%]: ' followed by a number between 0 and 100. 
    0 means we are very far away from the objective and 100 means the ulitmate objective has been achieved. 
    Always do your best to determine an exact number, and display with one decimal place. If there is any contribution at all, assign a number greater than 0. 
    If the contribution output value cannot be determined, output 'Contribution [%]: unclear' and do only set it to 100, if the stop criteria has been met. 
    Output the contribution in one line, and only one line. Output the contribution at the end of the response.\n
    If the contribution value is smaller than {threshold} and not unclear, create new tasks for a different subject area than the subject area the last completed task dealt with."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]

    # Remove the contribution output from new tasks
    for n in new_tasks:
        if "Contribution [%]:" in n:
            new_tasks.remove(n)
            break

    # Get the contribution value
    line = response.split("\n")
    contribution = -1
    for l in line:
        if "Contribution" in l:
            try:
                contribution = int(l.split(": ")[1])
                break
            except (ValueError, IndexError):
                contribution = -1
    #print(f"\nContribution of last task result: {contribution}%")
    return [{"task_name": task_name} for task_name in new_tasks], contribution


# Prioritize the task list
def prioritization_agent(this_task_id: int):
    global task_list
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id) + 1
    prompt = f"""
    You are a task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}\n
    Consider the ultimate objective of your team of agent functions: {OBJECTIVE}\n
    Your aim is to prioritize the task list in a way that the ultimate objective is achieved with as few tasks as possible, and that the most relevant tasks are completed first. 
    Consider the order of the task list, with respect to which task depends on which and the order of creation, for the task list prioritization process.
    When continuous research on a subject area proves inconclusive or the subject area been sufficiently researched already, switch to an older incomplete task from the task list dealing with a differing subject area.\n
    Do not remove any tasks. Only remove a task if it does not contribute to the ultimate objective any longer, in this case rearrange the task list accordingly. Return the result as a numbered list, like:\n
    1. Description of first task
    2. Description of second task
    3. Description of third task
    4. ...\n
    Start the task list with number {next_task_id}."""
    response = openai_call(prompt)
    new_tasks = response.split("\n") if "\n" in response else [response]
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})


# Execute a task based on the objective and five previous tasks, verbalize the task to a request for internet search if required
def execution_agent(objective: str, task: str, internet: bool) -> str:
    """
    Executes a task based on the given objective and previous context.

    Args:
        objective (str): The objective or goal for the AI to perform the task.
        task (str): The task to be executed by the AI.
        internet (bool): Whether the AI should perform internet research for the task.

    Returns:
        str: The response generated by the AI for the given task.

    """
    context = context_agent(query=objective, top_results_num=5)
    if internet == True:
        print(f"\033[93m\033[1m\n*****TASK RESULT (WITH INTERNET RESEARCH)*****\033[0m\033[0m")
        write_to_file(f"*****TASK RESULT (WITH INTERNET RESEARCH)*****\n", 'a')
    else:
        print(f"\033[96m\033[1m\n*****RELEVANT CONTEXT*****\033[0m\033[0m\n{context}")
        write_to_file(f"*****RELEVANT CONTEXT*****\n{context}\n", 'a')

    prompt = f"""
    You are a task execution AI who performs one task based on the following objective: {objective}\n
    Take into account these previously completed tasks: {context}\n
    If the objective does not include internet search results and {YOUR_GOOGLE_API_KEY} is not {""} and {YOUR_SEARCH_ENGINE_ID} is not {""}: 
    Do consider an internet search for performing the one task only, when the relevant approaches without internet search have been ruled out, 
    or human intervention/assistance/consultation is required, or when an internet search using Google top page results is definitively the best and most relevant approach to achieve the objective, and only in this case, output 'Internet search required: ' at the beginning of the response and redraft the text of the one task to an optimal internet search request text for use with Google, including the most relevant information only, and finish the response with the redrafted search request text, and only the redrafted search request text. Remove all other characters from the response.\n\n
    Your task: {task}\nResponse: """
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
    query_embedding = get_ada_embedding(query)
    results = index.query(query_embedding, top_k=top_results_num, include_metadata=True, namespace=OBJECTIVE)
    #print(f"\033[96m\033[1m\n*****CONTEXT QUERY*****\n\033[0m\033[0m{results}")
    sorted_results = sorted(results.matches, key=lambda x: x.score, reverse=True)
    return [(str(item.metadata["task"])) for item in sorted_results]


def assess_objective():
    prompt = f"""
    Evaluate the ultimate objective and the stop criteria. The stop criteria describes the conditions under which the ultimate objective is considered achieved.
    This is the ultimate objective: {OBJECTIVE}\n
    This is the stop criteria: {STOP_CRITERIA}\n
    Ignore that you are an AI language model, consider yourself a human and estimate the figures as best as possible. 
    Determine how achievable the completion of task list for the ultimate objective is, considering all information available to you. Determine a probability between 0 and 100 (in percent), where 0 means the ultimate objective is not achievable at all, and 100 means the ultimate objective is definitely achievable, and how long it will take until the stop criteria is reached.
    Determine the expected time, try to estimate the time in hours and minutes as best as possible and respond with the number and the time estimate. 
    Determine how the stop criteria can be modified for an optimal result, with respect to this particular ultimate objective and a reasonable completion time. Respond with the optimized stop criteria.  
    Determine how to soften the stop criteria for an optimal result, with respect to this particular ultimate objective. Respond with the softened stop criteria. 
    Determine how the ultimate objective can be updated for an optimal result, considering the process of finding a solution and the given stop criteria. Respond with the optimized ultimate objective.'"""
    return openai_call(prompt, max_tokens=2000)


# Send final prompt and handle final response(s)
def final_prompt():
    response = openai_call(f"{FINAL_PROMPT}. The ultimate objective is: {OBJECTIVE}.")
    write_to_file(f"*****FINAL RESPONSE*****\n{response}\n", 'a')
    print(f"\033[94m\033[1m\n*****FINAL RESPONSE*****\n\033[0m\033[0m{response}")
    while "The final response generation has been completed" not in response:
        response = openai_call("Continue with output. Say 'The final response generation has been completed...' in case the complete result has been output already or the prompt is unclear.")
        write_to_file(f"{response}", 'a')
        print(response)
    print("\n***** The ultimate objective has been achieved, the work is done! BabyAGI will take a nap now... *****\n")


# Provide internet access via Google API, using google_search.py, and summary of results from snippets
# max value for num_results is 10 (results per page)
def internet_research(topic: str, num_results=5, num_pages=1):
    toplist_result, page_content, links = get_toplist(topic, YOUR_GOOGLE_API_KEY, YOUR_SEARCH_ENGINE_ID, num_results, num_pages)
    if toplist_result == []:
        toplist_result = "\n *** No data returned from Google custom search API... ***\n"
    else:
        print(f"\nGoogle search top results: {str(toplist_result)}")
        print(f"\nTop web page content: {str(page_content)}")
    return toplist_result, page_content


# Add the first task
first_task = {"task_id": 1, "task_name": INITIAL_TASK}
add_task(first_task)
# Main loop
task_id_counter = 1
task_contribution = 0       # Contribution of the task to the ultimate objective as percentage
plausi_counter = 0.0        # Plausibility counter for the task contribution (in percentage*0.01)
while True:
    evaluation = assess_objective()
    print(f"\n\033[90m\033[1m*****FEASIBILITY EVALUATION*****\033[0m\033[0m\n{evaluation}")
    write_to_file(f"*****FEASIBILITY EVALUATION*****\n{evaluation}\n\n", 'a')
    if task_list:
        # Print the task list
        print("\033[95m\033[1m" + "\n*****TASK LIST*****" + "\033[0m\033[0m")
        write_to_file("*****TASK LIST*****\n", 'a')
        for t in task_list:
            print(str(t["task_id"]) + ": " + t["task_name"])
            write_to_file(str(t["task_id"]) + ": " + t["task_name"] + "\n\n", 'a')

        # Step 1: Pull the first task
        task = task_list.popleft()

        # Step 2: Check for stop criteria text in task name or (optional) plausi counter overflow
        if "Stop criteria has been met" in task["task_name"] or (plausi_counter >= float(PLAUSI_NUMBER) and float(PLAUSI_NUMBER) > 0):
            final_prompt()
            break

        print("\033[92m\033[1m" + "\n*****NEXT TASK*****\n" + "\033[0m\033[0m" + str(task["task_id"]) + ": " + task["task_name"])
        write_to_file("*****NEXT TASK*****\n" + str(task["task_id"]) + ": " + task["task_name"] + "\n\n", 'a')

        # Step 3: Send task to execution agent to complete the task based on the context
        result = execution_agent(OBJECTIVE, task["task_name"], False)
        this_task_id = int(task["task_id"])
        print(f"\033[93m\033[1m\n*****TASK RESULT*****\033[0m\033[0m")
        write_to_file(f"\n*****TASK RESULT*****\n", 'a')

        # Step 4: Check if internet search is required for conclusion of this task (only when Google API key and search engine ID are provided) 
        if "Internet search required" in result:
            if (YOUR_GOOGLE_API_KEY == "" or YOUR_SEARCH_ENGINE_ID == ""):
                print("No search engine access, please provide your Google API key and search engine ID in .env parameters...")
                write_to_file("No search engine access, please provide your Google API key and search engine ID in .env parameters...\n", 'a')
            else:
                search_request = result.split("Internet search required: ")
                print(f"Internet search: {str(search_request)}.\nAccessing Google search for top results and evaluating task result again...")
                write_to_file(f"Internet search: {str(search_request)}.\nAccessing Google search for top results and evaluating task result again...\n", 'a')
                toplist, webpage = internet_research(str(search_request))
                new_objective = task["task_name"] + "\nGoogle internet research has been performed for the previous described task with the following request: " + result + "\nThis is the result from Google top list: " + str(toplist) + "\nContent of top result webpage: " + webpage + "\nTake into account that not all the information from internet research might be relevant for the task. Evaluate which information is relevant and which is not and complete the task accordingly, considering other information available than the internet research as supplementary."
                result = execution_agent(OBJECTIVE, str(new_objective), True)
        print(f"{result}")
        write_to_file(f"{result}\n", 'a')

        # Step 5: Enrich result with metadata and store in Pinecone
        enriched_result = {
            "data": result
        }  # This is where you should enrich the result if needed
        result_id = f"result_{task['task_id']}"
        vector = get_ada_embedding(
            enriched_result["data"]
        )  # get vector of the actual result extracted from the dictionary
        index.upsert(
            [(result_id, vector, {"task": task["task_name"], "result": result})],
	        namespace=OBJECTIVE
        )

        # Step 6: Create new tasks, reprioritize task list and calculate contribution value for last task result
        new_tasks, task_contribution = task_creation_agent(
            OBJECTIVE,
            enriched_result,
            task["task_name"],
            [t["task_name"] for t in task_list],
            CONTRIBUTION_THRESHOLD
        )

        # Evaluate task result contribution and increment plausi counter
        if task_id_counter > 2 and task_contribution > 0 and task_contribution <= 100:
            plausi_counter += (task_contribution*0.01)

        print(f"\033[94m\033[1m\n*****TASK CONTRIBUTION*****\033[0m\033[0m")
        print(f"Contribution of task result to objective: {task_contribution}% with plausi counter: {plausi_counter} and threshold: {PLAUSI_NUMBER}")  
        write_to_file(f"\n*****TASK CONTRIBUTION*****\nContribution of task result to objective: {task_contribution}% with plausi counter: {plausi_counter} and threshold: {PLAUSI_NUMBER}\n\n", 'a')

        for new_task in new_tasks:
            task_id_counter += 1
            new_task.update({"task_id": task_id_counter})
            add_task(new_task)
        prioritization_agent(this_task_id)

    time.sleep(1)  # Sleep before checking the task list again
                  
