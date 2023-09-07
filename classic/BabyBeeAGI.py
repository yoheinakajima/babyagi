###### This is a modified version of OG BabyAGI, called BabyBeeAGI (future modifications will follow the pattern "Baby<animal>AGI"). This version requires GPT-4, it's very slow, and often errors out.######
######IMPORTANT NOTE: I'm sharing this as a framework to build on top of (with lots of errors for improvement), to facilitate discussion around how to improve these. This is NOT for people who are looking for a complete solution that's ready to use. ######

import openai
import litellm
import pinecone
import time
import requests
from bs4 import BeautifulSoup
from collections import deque
from typing import Dict, List
import re
import ast
import json
from serpapi import GoogleSearch

### SET THESE 4 VARIABLES ##############################

# Add your API keys here
OPENAI_API_KEY = ""
SERPAPI_API_KEY = "" #If you include SERPAPI KEY, this will enable web-search. If you don't, it will automatically remove web-search capability.

# Set variables
OBJECTIVE = "You are an AI. Make the world a better place."
YOUR_FIRST_TASK = "Develop a task list."

### UP TO HERE ##############################

# Configure OpenAI and SerpAPI client
openai.api_key = OPENAI_API_KEY
if SERPAPI_API_KEY:
  serpapi_client = GoogleSearch({"api_key": SERPAPI_API_KEY})
  websearch_var = "[web-search] "
else:
  websearch_var = ""

# Initialize task list
task_list = []

# Initialize session_summary
session_summary = ""

### Task list functions ##############################
def add_task(task: Dict):
    task_list.append(task)

def get_task_by_id(task_id: int):
    for task in task_list:
        if task["id"] == task_id:
            return task
    return None

def get_completed_tasks():
    return [task for task in task_list if task["status"] == "complete"]

### Tool functions ##############################
def text_completion_tool(prompt: str):
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.5,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text.strip()

def web_search_tool(query: str):
    search_params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num":3
    }
    search_results = GoogleSearch(search_params)
    results = search_results.get_dict()

    return str(results["organic_results"])

def web_scrape_tool(url: str):
    response = requests.get(url)
    print(response)
    soup = BeautifulSoup(response.content, "html.parser")
    result = soup.get_text(strip=True)+"URLs: "
    for link in soup.findAll('a', attrs={'href': re.compile("^https://")}):
      result+= link.get('href')+", "
    return result

### Agent functions ##############################
def execute_task(task, task_list, OBJECTIVE):
    global task_id_counter
    # Check if dependent_task_id is complete
    if task["dependent_task_id"]:
        dependent_task = get_task_by_id(task["dependent_task_id"])
        if not dependent_task or dependent_task["status"] != "complete":
            return

    # Execute task
    
    print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
    print(str(task['id'])+": "+str(task['task'])+" ["+str(task['tool']+"]"))
    task_prompt = f"Complete your assigned task based on the objective: {OBJECTIVE}. Your task: {task['task']}"
    if task["dependent_task_id"]:
        dependent_task_result = dependent_task["result"]
        task_prompt += f"\nThe previous task ({dependent_task['id']}. {dependent_task['task']}) result: {dependent_task_result}"

    task_prompt += "\nResponse:"
    ##print("###task_prompt: "+task_prompt)
    if task["tool"] == "text-completion":
        result = text_completion_tool(task_prompt)
    elif task["tool"] == "web-search":
        result = web_search_tool(task_prompt)
    elif task["tool"] == "web-scrape":
        result = web_scrape_tool(str(task['task']))
    else:
        result = "Unknown tool"

    
    print("\033[93m\033[1m"+"\n*****TASK RESULT*****\n"+"\033[0m\033[0m")
    print_result = result[0:2000]
    if result != result[0:2000]:
      print(print_result+"...")
    else:
      print(result)
    # Update task status and result
    task["status"] = "complete"
    task["result"] = result
    task["result_summary"] = summarizer_agent(result)

    # Update session_summary
    session_summary = overview_agent(task["id"])

    # Increment task_id_counter
    task_id_counter += 1

    # Update task_manager_agent of tasks
    task_manager_agent(
        OBJECTIVE,
        result,
        task["task"],
        [t["task"] for t in task_list if t["status"] == "incomplete"],
        task["id"]  
    )


def task_manager_agent(objective: str, result: str, task_description: str, incomplete_tasks: List[str], current_task_id : int) -> List[Dict]:
    global task_list
    original_task_list = task_list.copy()
    minified_task_list = [{k: v for k, v in task.items() if k != "result"} for task in task_list]
    result = result[0:4000] #come up with better solution later.

    prompt = (
        f"You are a task management AI tasked with cleaning the formatting of and reprioritizing the following tasks: {minified_task_list}. "
        f"Consider the ultimate objective of your team: {OBJECTIVE}. "
        f"Do not remove any tasks. Return the result as a JSON-formatted list of dictionaries.\n"
        f"Create new tasks based on the result of last task if necessary for the objective. Limit tasks types to those that can be completed with the available tools listed below. Task description should be detailed."
        f"The maximum task list length is 7. Do not add an 8th task."
        f"The last completed task has the following result: {result}. "
        f"Current tool option is [text-completion] {websearch_var} and [web-scrape] only."# web-search is added automatically if SERPAPI exists
        f"For tasks using [web-scrape], provide only the URL to scrape as the task description. Do not provide placeholder URLs, but use ones provided by a search step or the initial objective."
        #f"If the objective is research related, use at least one [web-search] with the query as the task description, and after, add up to three URLs from the search result as a task with [web-scrape], then use [text-completion] to write a comprehensive summary of each site thas has been scraped.'"
        f"For tasks using [web-search], provide the search query, and only the search query to use (eg. not 'research waterproof shoes, but 'waterproof shoes')"
        f"dependent_task_id should always be null or a number."
        f"Do not reorder completed tasks. Only reorder and dedupe incomplete tasks.\n"
        f"Make sure all task IDs are in chronological order.\n"
        f"Do not provide example URLs for [web-scrape].\n"
        f"Do not include the result from the last task in the JSON, that will be added after..\n"
        f"The last step is always to provide a final summary report of all tasks.\n"
        f"An example of the desired output format is: "
        "[{\"id\": 1, \"task\": \"https://untapped.vc\", \"tool\": \"web-scrape\", \"dependent_task_id\": null, \"status\": \"incomplete\", \"result\": null, \"result_summary\": null}, {\"id\": 2, \"task\": \"Analyze the contents of...\", \"tool\": \"text-completion\", \"dependent_task_id\": 1, \"status\": \"incomplete\", \"result\": null, \"result_summary\": null}, {\"id\": 3, \"task\": \"Untapped Capital\", \"tool\": \"web-search\", \"dependent_task_id\": null, \"status\": \"incomplete\", \"result\": null, \"result_summary\": null}]."
    )
    print("\033[90m\033[3m" + "\nRunning task manager agent...\n" + "\033[0m")
    response = litellm.completion(
        model="gpt-4",
        messages=[
            {
                "role": "system",
                "content": "You are a task manager AI."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Extract the content of the assistant's response and parse it as JSON
    result = response["choices"][0]["message"]["content"]
    print("\033[90m\033[3m" + "\nDone!\n" + "\033[0m")
    try:
      task_list = json.loads(result)
    except Exception as error:
      print(error)
    # Add the 'result' field back in
    for updated_task, original_task in zip(task_list, original_task_list):
        if "result" in original_task:
            updated_task["result"] = original_task["result"]
    task_list[current_task_id]["result"]=result
    #print(task_list)
    return task_list



def summarizer_agent(text: str) -> str:
    text = text[0:4000]
    prompt = f"Please summarize the following text:\n{text}\nSummary:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.5,
        max_tokens=100,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].text.strip()


def overview_agent(last_task_id: int) -> str:
    global session_summary

    completed_tasks = get_completed_tasks()
    completed_tasks_text = "\n".join(
        [f"{task['id']}. {task['task']} - {task['result_summary']}" for task in completed_tasks]
    )

    prompt = f"Here is the current session summary:\n{session_summary}\nThe last completed task is task {last_task_id}. Please update the session summary with the information of the last task:\n{completed_tasks_text}\nUpdated session summary, which should describe all tasks in chronological order:"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        temperature=0.5,
        max_tokens=200,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )
    session_summary = response.choices[0].text.strip()
    return session_summary


### Main Loop ##############################

# Add the first task
first_task = {
    "id": 1,
    "task": YOUR_FIRST_TASK,
    "tool": "text-completion",
    "dependent_task_id": None,
    "status": "incomplete",
    "result": "",
    "result_summary": ""
}
add_task(first_task)

task_id_counter = 0
#Print OBJECTIVE
print("\033[96m\033[1m"+"\n*****OBJECTIVE*****\n"+"\033[0m\033[0m")
print(OBJECTIVE)

# Continue the loop while there are incomplete tasks
while any(task["status"] == "incomplete" for task in task_list):

    # Filter out incomplete tasks
    incomplete_tasks = [task for task in task_list if task["status"] == "incomplete"]

    if incomplete_tasks:
        # Sort tasks by ID
        incomplete_tasks.sort(key=lambda x: x["id"])

        # Pull the first task
        task = incomplete_tasks[0]

        # Execute task & call task manager from function
        execute_task(task, task_list, OBJECTIVE)

        # Print task list and session summary
        print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m")
        for t in task_list:
            dependent_task = ""
            if t['dependent_task_id'] is not None:
                dependent_task = f"\033[31m<dependency: #{t['dependent_task_id']}>\033[0m"
            status_color = "\033[32m" if t['status'] == "complete" else "\033[31m"
            print(f"\033[1m{t['id']}\033[0m: {t['task']} {status_color}[{t['status']}]\033[0m \033[93m[{t['tool']}] {dependent_task}\033[0m")
        print("\033[93m\033[1m" + "\n*****SESSION SUMMARY*****\n" + "\033[0m\033[0m")
        print(session_summary)

    time.sleep(1)  # Sleep before checking the task list again

### Objective complete ##############################

# Print the full task list if there are no incomplete tasks
if all(task["status"] != "incomplete" for task in task_list):
    print("\033[92m\033[1m" + "\n*****ALL TASKS COMPLETED*****\n" + "\033[0m\033[0m")
    for task in task_list:
        print(f"ID: {task['id']}, Task: {task['task']}, Result: {task['result']}")
