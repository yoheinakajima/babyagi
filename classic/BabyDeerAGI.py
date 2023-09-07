###### This is a modified version of OG BabyAGI, called BabyDeerAGI (modifications will follow the pattern "Baby<animal>AGI").######
######IMPORTANT NOTE: I'm sharing this as a framework to build on top of (with lots of room for improvement), to facilitate discussion around how to improve these. This is NOT for people who are looking for a complete solution that's ready to use. ######

import openai
import time
from datetime import datetime
import requests
from bs4 import BeautifulSoup
from collections import deque
from typing import Dict, List
import re
import ast
import json
from serpapi import GoogleSearch
from concurrent.futures import ThreadPoolExecutor
import time

### SET THESE 4 VARIABLES ##############################

# Add your API keys here
OPENAI_API_KEY = ""
SERPAPI_API_KEY = "" #[optional] web-search becomes available automatically when serpapi api key is provided

# Set variables
OBJECTIVE = "Research recent AI news and write a poem about your findings in the style of shakespeare."

#turn on user input (change to "True" to turn on user input tool)
user_input=False

### UP TO HERE ##############################

# Configure OpenAI and SerpAPI client
openai.api_key = OPENAI_API_KEY
if SERPAPI_API_KEY:
  serpapi_client = GoogleSearch({"api_key": SERPAPI_API_KEY})
  websearch_var = "[web-search] "
else:
  websearch_var = ""

if user_input == True:
  user_input_var = "[user-input]"
else:
  user_input_var = ""


# Initialize task list
task_list = []

# Initialize session_summary
session_summary = "OBJECTIVE: "+OBJECTIVE+"\n\n"

### Task list functions ##############################
def get_task_by_id(task_id: int):
    for task in task_list:
        if task["id"] == task_id:
            return task
    return None

# Print task list and session summary
def print_tasklist():
  p_tasklist="\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m"
  for t in task_list:
      dependent_task = ""
      if t['dependent_task_ids']:
          dependent_task = f"\033[31m<dependencies: {', '.join([f'#{dep_id}' for dep_id in t['dependent_task_ids']])}>\033[0m"
      status_color = "\033[32m" if t['status'] == "complete" else "\033[31m"
      p_tasklist+= f"\033[1m{t['id']}\033[0m: {t['task']} {status_color}[{t['status']}]\033[0m \033[93m[{t['tool']}] {dependent_task}\033[0m\n"
  print(p_tasklist)

### Tool functions ##############################
def text_completion_tool(prompt: str):
    messages = [
        {"role": "user", "content": prompt}
    ]
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages,
        temperature=0.2,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    return response.choices[0].message['content'].strip()


def user_input_tool(prompt: str):
    val = input(f"\n{prompt}\nYour response: ")
    return str(val)


def web_search_tool(query: str , dependent_tasks_output : str):
    
    if dependent_tasks_output != "":
      dependent_task = f"Use the dependent task output below as reference to help craft the correct search query for the provided task above. Dependent task output:{dependent_tasks_output}."
    else:
      dependent_task = "."
    query = text_completion_tool("You are an AI assistant tasked with generating a Google search query based on the following task: "+query+". If the task looks like a search query, return the identical search query as your response. " + dependent_task + "\nSearch Query:")
    print("\033[90m\033[3m"+"Search query: " +str(query)+"\033[0m")
    search_params = {
        "engine": "google",
        "q": query,
        "api_key": SERPAPI_API_KEY,
        "num":3 #edit this up or down for more results, though higher often results in OpenAI rate limits
    }
    search_results = GoogleSearch(search_params)
    search_results = search_results.get_dict()
    try:
      search_results = search_results["organic_results"]
    except:
      search_results = {}
    search_results = simplify_search_results(search_results)
    print("\033[90m\033[3m" + "Completed search. Now scraping results.\n" + "\033[0m")
    results = "";
    # Loop through the search results
    for result in search_results:
        # Extract the URL from the result
        url = result.get('link')
        # Call the web_scrape_tool function with the URL
        print("\033[90m\033[3m" + "Scraping: "+url+"" + "...\033[0m")
        content = web_scrape_tool(url, task)
        print("\033[90m\033[3m" +str(content[0:100])[0:100]+"...\n" + "\033[0m")
        results += str(content)+". "
    
    results = text_completion_tool(f"You are an expert analyst. Rewrite the following information as one report without removing any facts.\n###INFORMATION:{results}.\n###REPORT:")
    return results


def simplify_search_results(search_results):
    simplified_results = []
    for result in search_results:
        simplified_result = {
            "position": result.get("position"),
            "title": result.get("title"),
            "link": result.get("link"),
            "snippet": result.get("snippet")
        }
        simplified_results.append(simplified_result)
    return simplified_results


def web_scrape_tool(url: str, task:str):
    content = fetch_url_content(url)
    if content is None:
        return None

    text = extract_text(content)
    print("\033[90m\033[3m"+"Scrape completed. Length:" +str(len(text))+".Now extracting relevant info..."+"...\033[0m")
    info = extract_relevant_info(OBJECTIVE, text[0:5000], task)
    links = extract_links(content)

    #result = f"{info} URLs: {', '.join(links)}"
    result = info
    
    return result

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
}

def fetch_url_content(url: str):
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"Error while fetching the URL: {e}")
        return ""

def extract_links(content: str):
    soup = BeautifulSoup(content, "html.parser")
    links = [link.get('href') for link in soup.findAll('a', attrs={'href': re.compile("^https?://")})]
    return links

def extract_text(content: str):
    soup = BeautifulSoup(content, "html.parser")
    text = soup.get_text(strip=True)
    return text



def extract_relevant_info(objective, large_string, task):
    chunk_size = 3000
    overlap = 500
    notes = ""
    
    for i in range(0, len(large_string), chunk_size - overlap):
        chunk = large_string[i:i + chunk_size]
        
        messages = [
            {"role": "system", "content": f"You are an AI assistant."},
            {"role": "user", "content": f"You are an expert AI research assistant tasked with creating or updating the current notes. If the current note is empty, start a current-notes section by exracting relevant data to the task and objective from the chunk of text to analyze. If there is a current note, add new relevant info frol the chunk of text to analyze. Make sure the new or combined notes is comprehensive and well written. Here's the current chunk of text to analyze: {chunk}. ### Here is the current task: {task}.### For context, here is the objective: {OBJECTIVE}.### Here is the data we've extraced so far that you need to update: {notes}.### new-or-updated-note:"}
        ]

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=800,
            n=1,
            stop="###",
            temperature=0.7,
        )

        notes += response.choices[0].message['content'].strip()+". ";
    
    return notes

### Agent functions ##############################


def execute_task(task, task_list, OBJECTIVE):
    
    global session_summary
    global task_id_counter
    # Check if dependent_task_ids is not empty
    if task["dependent_task_ids"]:
      all_dependent_tasks_complete = True
      for dep_id in task["dependent_task_ids"]:
          dependent_task = get_task_by_id(dep_id)
          if not dependent_task or dependent_task["status"] != "complete":
              all_dependent_tasks_complete = False
              break
  
        
    # Execute task
    p_nexttask="\033[92m\033[1m"+"\n*****NEXT TASK ID:"+str(task['id'])+"*****\n"+"\033[0m\033[0m"
    p_nexttask += str(task['id'])+": "+str(task['task'])+" ["+str(task['tool']+"]")
    print(p_nexttask)
    task_prompt = f"Complete your assigned task based on the objective and only based on information provided in the dependent task output, if provided. \n###\nYour objective: {OBJECTIVE}. \n###\nYour task: {task['task']}"
    if task["dependent_task_ids"]:
      dependent_tasks_output = ""
      for dep_id in task["dependent_task_ids"]:
          dependent_task_output = get_task_by_id(dep_id)["output"]
          dependent_task_output = dependent_task_output[0:2000]
          dependent_tasks_output += f" {dependent_task_output}"
      task_prompt += f" \n###\ndependent tasks output: {dependent_tasks_output}  \n###\nYour task: {task['task']}\n###\nRESPONSE:"
    else:
      dependent_tasks_output="."

    # Use tool to complete the task
    if task["tool"] == "text-completion":
        task_output = text_completion_tool(task_prompt)
    elif task["tool"] == "web-search":
        task_output = web_search_tool(str(task['task']),str(dependent_tasks_output))
    elif task["tool"] == "web-scrape":
        task_output = web_scrape_tool(str(task['task']))
    elif task["tool"] == "user-input":
        task_output = user_input_tool(str(task['task']))

    

    # Find task index in the task_list
    task_index = next((i for i, t in enumerate(task_list) if t["id"] == task["id"]), None)

    # Mark task as complete and save output
    task_list[task_index]["status"] = "complete"
    task_list[task_index]["output"] = task_output

    # Print task output
    print("\033[93m\033[1m"+"\nTask Output (ID:"+str(task['id'])+"):"+"\033[0m\033[0m")
    print(task_output)
    # Add task output to session_summary
    session_summary += f"\n\nTask {task['id']} - {task['task']}:\n{task_output}"

def task_ready_to_run(task, task_list):
    return all([get_task_by_id(dep_id)["status"] == "complete" for dep_id in task["dependent_task_ids"]])


task_list = []

def task_creation_agent(objective: str) -> List[Dict]:
    global task_list
    minified_task_list = [{k: v for k, v in task.items() if k != "result"} for task in task_list]

    prompt = (
        f"You are an expert task creation AI tasked with creating a  list of tasks as a JSON array, considering the ultimate objective of your team: {OBJECTIVE}. "
        f"Create new tasks based on the objective. Limit tasks types to those that can be completed with the available tools listed below. Task description should be detailed."
        f"Current tool options are [text-completion] {websearch_var} {user_input_var}." # web-search is added automatically if SERPAPI exists
        f"For tasks using [web-search], provide the search query, and only the search query to use (eg. not 'research waterproof shoes, but 'waterproof shoes'). Result will be a summary of relevant information from the first few articles."
        f"When requiring multiple searches, use the [web-search] multiple times. This tool will use the dependent task result to generate the search query if necessary."
        f"Use [user-input] sparingly and only if you need to ask a question to the user who set up the objective. The task description should be the question you want to ask the user.')"
        f"dependent_task_ids should always be an empty array, or an array of numbers representing the task ID it should pull results from."
        f"Make sure all task IDs are in chronological order.\n"
        f"EXAMPLE OBJECTIVE=Look up AI news from today (May 27, 2023) and write a poem."
        "TASK LIST=[{\"id\":1,\"task\":\"AI news today\",\"tool\":\"web-search\",\"dependent_task_ids\":[],\"status\":\"incomplete\",\"result\":null,\"result_summary\":null},{\"id\":2,\"task\":\"Extract key points from AI news articles\",\"tool\":\"text-completion\",\"dependent_task_ids\":[1],\"status\":\"incomplete\",\"result\":null,\"result_summary\":null},{\"id\":3,\"task\":\"Generate a list of AI-related words and phrases\",\"tool\":\"text-completion\",\"dependent_task_ids\":[2],\"status\":\"incomplete\",\"result\":null,\"result_summary\":null},{\"id\":4,\"task\":\"Write a poem using AI-related words and phrases\",\"tool\":\"text-completion\",\"dependent_task_ids\":[3],\"status\":\"incomplete\",\"result\":null,\"result_summary\":null},{\"id\":5,\"task\":\"Final summary report\",\"tool\":\"text-completion\",\"dependent_task_ids\":[1,2,3,4],\"status\":\"incomplete\",\"result\":null,\"result_summary\":null}]"
        f"OBJECTIVE={OBJECTIVE}"
        f"TASK LIST="
    )

    print("\033[90m\033[3m" + "\nInitializing...\n" + "\033[0m")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "system",
                "content": "You are a task creation AI."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_tokens=1500,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0
    )

    # Extract the content of the assistant's response and parse it as JSON
    result = response["choices"][0]["message"]["content"]
    try:
        task_list = json.loads(result)
    except Exception as error:
        print(error)

    return task_list

##### START MAIN LOOP########

#Print OBJECTIVE
print("\033[96m\033[1m"+"\n*****OBJECTIVE*****\n"+"\033[0m\033[0m")
print(OBJECTIVE)

# Initialize task_id_counter
task_id_counter = 1

# Run the task_creation_agent to create initial tasks
task_list = task_creation_agent(OBJECTIVE)
print_tasklist()

# Create a ThreadPoolExecutor
with ThreadPoolExecutor() as executor:
    while True:
        tasks_submitted = False
        for task in task_list:
            if task["status"] == "incomplete" and task_ready_to_run(task, task_list):
                future = executor.submit(execute_task, task, task_list, OBJECTIVE)
                task["status"] = "running"
                tasks_submitted = True

        if not tasks_submitted and all(task["status"] == "complete" for task in task_list):
            break

        time.sleep(5)

# Print session summary
print("\033[96m\033[1m"+"\n*****SAVING FILE...*****\n"+"\033[0m\033[0m")
file = open(f'output/output_{datetime.now().strftime("%d_%m_%Y_%H_%M_%S")}.txt', 'w')
file.write(session_summary)
file.close()
print("...file saved.")
print("END")
