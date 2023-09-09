###### This is a modified version of OG BabyAGI, called BabyCatAGI (future modifications will follow the pattern "Baby<animal>AGI"). This version requires GPT-4, it's very slow, and often errors out.######
######IMPORTANT NOTE: I'm sharing this as a framework to build on top of (with lots of errors for improvement), to facilitate discussion around how to improve these. This is NOT for people who are looking for a complete solution that's ready to use. ######

import openai
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
from collections import deque
from typing import Dict, List
import re
import ast
import json
from serpapi import GoogleSearch

### SET THESE 4 VARIABLES ##############################

# Add your API keys here
OPENAI_API_KEY = ""
SERPAPI_API_KEY = "" #If you include SERPAPI KEY, this will enable web-search using SERP Index. If you don't, it will autoatically using Google Scrape.

# Set variables
OBJECTIVE = "Research experts at scaling NextJS and their Twitter accounts."
YOUR_FIRST_TASK = "Develop a task list." #you can provide additional instructions here regarding the task list.

### UP TO HERE ##############################

# Configure OpenAI and SerpAPI client
openai.api_key = OPENAI_API_KEY

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


# Print task list and session summary
def print_tasklist():
  print("\033[95m\033[1m" + "\n*****TASK LIST*****\n" + "\033[0m")
  for t in task_list:
      dependent_task = ""
      if t['dependent_task_ids']:
          dependent_task = f"\033[31m<dependencies: {', '.join([f'#{dep_id}' for dep_id in t['dependent_task_ids']])}>\033[0m"
      status_color = "\033[32m" if t['status'] == "complete" else "\033[31m"
      print(f"\033[1m{t['id']}\033[0m: {t['task']} {status_color}[{t['status']}]\033[0m \033[93m[{t['tool']}] {dependent_task}\033[0m")

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


def web_search_tool(query: str):
    search_results = {}
    if SERPAPI_API_KEY:
        # USING SERP API
        search_params = {
            "engine": "google",
            "q": query,
            "api_key": SERPAPI_API_KEY,
            "num":5 #edit this up or down for more results, though higher often results in OpenAI rate limits
        }
        search_results = GoogleSearch(search_params)
        search_results = search_results.get_dict()
        try:
            search_results = search_results["organic_results"]
        except:
            search_results = {}
        search_results = simplify_search_results(search_results)
    else:
        # USING GOOGLE SCRAPER
        search_results = scrape_google_results(query)
    
    print("\033[90m\033[3m" + "Completed search. Now scraping results.\n" + "\033[0m")
    results = ""
    # Loop through the search results
    for result in search_results:
        # Extract the URL from the result
        url = result.get('link')
        # Call the web_scrape_tool function with the URL
        print("\033[90m\033[3m" + "Scraping: "+url+"" + "...\033[0m")
        content = web_scrape_tool(url, task)
        print("\033[90m\033[3m" +str(content[0:100])[0:100]+"...\n" + "\033[0m")
        results += str(content)+". "
    
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

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36"
}

def scrape_google_results(search_query):
    url = f"https://www.google.com/search?q={search_query}"
    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, 'html.parser')

    search_results = []
    # Find the main div element
    main_div = soup.find('div', id='main')
    nested_div = main_div.find_all('div')
    for div in nested_div:
        a_tags = div.find_all('a')
        for a_tag in a_tags:
            href = a_tag.get('href')
            if href and href.startswith('/url?esrc=s&q=&rct=j&sa=U&url='):
                # Parse the URL and extract the query parameters
                parsed_url = urlparse(href)
                query_params = parse_qs(parsed_url.query)
                # Extract the value after 'url='
                if 'url' in query_params:
                    url_value = query_params['url'][0]
                    search_results.append(url_value)
                else:
                    print("No 'url' parameter found in the URL.")
    unique_results = list(set(search_results))
    # simplify the results to match the format of the SERP API results
    simplified_results = []
    for result in unique_results:
        simplified_result = {
            "link": result,
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
            {"role": "system", "content": f"Objective: {objective}\nCurrent Task:{task}"},
            {"role": "user", "content": f"Analyze the following text and extract information relevant to our objective and current task, and only information relevant to our objective and current task. If there is no relevant information do not say that there is no relevant informaiton related to our objective. ### Then, update or start our notes provided here (keep blank if currently blank): {notes}.### Text to analyze: {chunk}.### Updated Notes:"}
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
    print("\033[92m\033[1m"+"\n*****NEXT TASK*****\n"+"\033[0m\033[0m")
    print(str(task['id'])+": "+str(task['task'])+" ["+str(task['tool']+"]"))
    task_prompt = f"Complete your assigned task based on the objective and only based on information provided in the dependent task output, if provided. Your objective: {OBJECTIVE}. Your task: {task['task']}"
    if task["dependent_task_ids"]:
      dependent_tasks_output = ""
      for dep_id in task["dependent_task_ids"]:
          dependent_task_output = get_task_by_id(dep_id)["output"]
          dependent_task_output = dependent_task_output[0:2000]
          dependent_tasks_output += f" {dependent_task_output}"
      task_prompt += f" Your dependent tasks output: {dependent_tasks_output}\n OUTPUT:"

    # Use tool to complete the task
    if task["tool"] == "text-completion":
        task_output = text_completion_tool(task_prompt)
    elif task["tool"] == "web-search":
        task_output = web_search_tool(str(task['task']))
    elif task["tool"] == "web-scrape":
        task_output = web_scrape_tool(str(task['task']), "Scrape this link: "+str(task['task']))

    # Find task index in the task_list
    task_index = next((i for i, t in enumerate(task_list) if t["id"] == task["id"]), None)

    # Mark task as complete and save output
    task_list[task_index]["status"] = "complete"
    task_list[task_index]["output"] = task_output

    # Print task output
    print("\033[93m\033[1m"+"\nTask Output:"+"\033[0m\033[0m")
    print(task_output)

    # Add task output to session_summary
    global session_summary
    session_summary += f"\n\nTask {task['id']} - {task['task']}:\n{task_output}"



task_list = []

def task_creation_agent(objective: str) -> List[Dict]:
    global task_list
    minified_task_list = [{k: v for k, v in task.items() if k != "result"} for task in task_list]

    prompt = (
        f"You are a task creation AI tasked with creating a list of tasks as a JSON array, considering the ultimate objective of your team: {OBJECTIVE}. "
        f"Create new tasks based on the objective. Limit tasks types to those that can be completed with the available tools listed below. Task description should be detailed."
        f"Current tool option is [text-completion] [web-scrape] [web-search] and only."
        f"For tasks using [web-search], provide the search query, and only the search query to use (eg. not 'research waterproof shoes, but 'waterproof shoes')"
        f"dependent_task_ids should always be an empty array, or an array of numbers representing the task ID it should pull results from."
        f"Make sure all task IDs are in chronological order.\n"
        f"The last step is always to provide a final summary report including tasks executed and summary of knowledge acquired.\n"
        f"Do not create any summarizing steps outside of the last step..\n"
        f"An example of the desired output format is: "
        "[{\"id\": 1, \"task\": \"https://untapped.vc\", \"tool\": \"web-scrape\", \"dependent_task_ids\": [], \"status\": \"incomplete\", \"result\": null, \"result_summary\": null}, {\"id\": 2, \"task\": \"Consider additional insights that can be reasoned from the results of...\", \"tool\": \"text-completion\", \"dependent_task_ids\": [1], \"status\": \"incomplete\", \"result\": null, \"result_summary\": null}, {\"id\": 3, \"task\": \"Untapped Capital\", \"tool\": \"web-search\", \"dependent_task_ids\": [], \"status\": \"incomplete\", \"result\": null, \"result_summary\": null}].\n"
        f"JSON TASK LIST="
    )

    print("\033[90m\033[3m" + "\nInitializing...\n" + "\033[0m")
    print("\033[90m\033[3m" + "Analyzing objective...\n" + "\033[0m")
    print("\033[90m\033[3m" + "Running task creation agent...\n" + "\033[0m")
    response = openai.ChatCompletion.create(
        model="gpt-4",
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
    print("\033[90m\033[3m" + "\nDone!\n" + "\033[0m")
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
task_id_counter = 0

# Run the task_creation_agent to create initial tasks
task_list = task_creation_agent(OBJECTIVE)
print_tasklist()

# Execute tasks in order
while len(task_list) > task_id_counter:
    for task in task_list:
        if task["status"] == "incomplete":
            execute_task(task, task_list, OBJECTIVE)
            print_tasklist()
            task_id_counter += 1
            break

# Print session summary
print("\033[96m\033[1m"+"\n*****SESSION SUMMARY*****\n"+"\033[0m\033[0m")
print(session_summary)
