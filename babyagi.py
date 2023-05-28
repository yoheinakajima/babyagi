#!/usr/bin/env python3
from dotenv import load_dotenv

# Load default environment variables (.env)
load_dotenv()

import os
import hashlib
import pickle
import subprocess
import select
import pty
import time
import logging
from collections import deque
from typing import Dict, List
import importlib
import openai
import tiktoken as tiktoken
import re
import json

#[Test]
#while True:
#    time.sleep(100)

# Engine configuration
BABY_COMMAND_AGI_FOLDER = "/app"

# Model: GPT, LLAMA, HUMAN, etc.
LLM_MODEL = os.getenv("LLM_MODEL", os.getenv("OPENAI_API_MODEL", "gpt-4")).lower()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
if not (LLM_MODEL.startswith("llama") or LLM_MODEL.startswith("human")):
    assert OPENAI_API_KEY, "\033[91m\033[1m" + "OPENAI_API_KEY environment variable is missing from .env" + "\033[0m\033[0m"

# Table config
RESULTS_STORE_NAME = os.getenv("RESULTS_STORE_NAME", os.getenv("TABLE_NAME", ""))
assert RESULTS_STORE_NAME, "\033[91m\033[1m" + "RESULTS_STORE_NAME environment variable is missing from .env" + "\033[0m\033[0m"

# Run configuration
INSTANCE_NAME = os.getenv("INSTANCE_NAME", os.getenv("BABY_NAME", "BabyCommandAGI"))
COOPERATIVE_MODE = "none"
# If USER_INPUT_LLM is set to True, the LLM will automatically respond if there is a confirmation when executing a command, 
# but be aware that this will increase the number of times the LLM is used and increase the cost of the API, etc.
USER_INPUT_LLM = True
JOIN_EXISTING_OBJECTIVE = False
MAX_TOKEN = 5000
MAX_STRING_LENGTH = 6000

# Goal configuration
OBJECTIVE = os.getenv("OBJECTIVE", "")
INITIAL_TASK = os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", ""))

# Model configuration
OPENAI_TEMPERATURE = float(os.getenv("OPENAI_TEMPERATURE", 0.0))

#Set Variables
hash_object = hashlib.sha1(OBJECTIVE.encode())
hex_dig = hash_object.hexdigest()
table_name = f"{hex_dig[:8]}-{RESULTS_STORE_NAME}"
TASK_LIST_FILE = f"{BABY_COMMAND_AGI_FOLDER}/data/{table_name}_task_list.pkl"
EXECUTED_TASK_LIST_FILE = f"{BABY_COMMAND_AGI_FOLDER}/data/{table_name}_executed_task_list.pkl"
PWD_FILE = f"{BABY_COMMAND_AGI_FOLDER}/pwd/{table_name}"
ENV_DUMP_FILE = f"{BABY_COMMAND_AGI_FOLDER}/env_dump/{table_name}"

# logger
logging.basicConfig(format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=f"{BABY_COMMAND_AGI_FOLDER}/log/{table_name}.log",
                    filemode='a',
                    level=logging.DEBUG)
def log(message):
    print(message)
    logging.info(message)

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

        OBJECTIVE, INITIAL_TASK, LLM_MODEL, DOTENV_EXTENSIONS, INSTANCE_NAME, COOPERATIVE_MODE, JOIN_EXISTING_OBJECTIVE = parse_arguments()

# Human mode extension
# Gives human input to babyagi
if LLM_MODEL.startswith("human"):
    if can_import("extensions.human_mode"):
        from extensions.human_mode import user_input_await

# Load additional environment variables for enabled extensions
# TODO: This might override the following command line arguments as well:
#    OBJECTIVE, INITIAL_TASK, LLM_MODEL, INSTANCE_NAME, COOPERATIVE_MODE, JOIN_EXISTING_OBJECTIVE
if DOTENV_EXTENSIONS:
    if can_import("extensions.dotenvext"):
        from extensions.dotenvext import load_dotenv_extensions

        load_dotenv_extensions(DOTENV_EXTENSIONS)

# TODO: There's still work to be done here to enable people to get
# defaults from dotenv extensions, but also provide command line
# arguments to override them

# Extensions support end

log("\033[95m\033[1m" + "\n*****CONFIGURATION*****\n" + "\033[0m\033[0m")
log(f"Name  : {INSTANCE_NAME}")
log(f"Mode  : {'alone' if COOPERATIVE_MODE in ['n', 'none'] else 'local' if COOPERATIVE_MODE in ['l', 'local'] else 'distributed' if COOPERATIVE_MODE in ['d', 'distributed'] else 'undefined'}")
log(f"LLM   : {LLM_MODEL}")

# Check if we know what we are doing
assert OBJECTIVE, "\033[91m\033[1m" + "OBJECTIVE environment variable is missing from .env" + "\033[0m\033[0m"
assert INITIAL_TASK, "\033[91m\033[1m" + "INITIAL_TASK environment variable is missing from .env" + "\033[0m\033[0m"

# Save and load functions for task_list and executed_task_list
def save_data(data, filename):
  with open(filename, 'wb') as f:
    pickle.dump(data, f)

def load_data(filename):
  if os.path.exists(filename):
    with open(filename, 'rb') as f:
      return pickle.load(f)
  return deque([])

LLAMA_MODEL_PATH = os.getenv("LLAMA_MODEL_PATH", "models/llama-13B/ggml-model.bin")
if LLM_MODEL.startswith("llama"):
    if can_import("llama_cpp"):
        from llama_cpp import Llama

        log(f"LLAMA : {LLAMA_MODEL_PATH}" + "\n")
        assert os.path.exists(LLAMA_MODEL_PATH), "\033[91m\033[1m" + f"Model can't be found." + "\033[0m\033[0m"

        CTX_MAX = 1024
        LLAMA_THREADS_NUM = int(os.getenv("LLAMA_THREADS_NUM", 8))

        log('Initialize model for evaluation')
        llm = Llama(
            model_path=LLAMA_MODEL_PATH,
            n_ctx=CTX_MAX,
            n_threads=LLAMA_THREADS_NUM,
            n_batch=512,
            use_mlock=False,
        )

        log(
            "\033[91m\033[1m"
            + "\n*****USING LLAMA.CPP. POTENTIALLY SLOW.*****"
            + "\033[0m\033[0m"
        )
    else:
        log(
            "\033[91m\033[1m"
            + "\nLlama LLM requires package llama-cpp. Falling back to GPT-3.5-turbo."
            + "\033[0m\033[0m"
        )
        LLM_MODEL = "gpt-4"

if LLM_MODEL.startswith("gpt-4"):
    log(
        "\033[91m\033[1m"
        + "\n*****USING GPT-4. POTENTIALLY EXPENSIVE. MONITOR YOUR COSTS*****"
        + "\033[0m\033[0m"
    )

if LLM_MODEL.startswith("human"):
    log(
        "\033[91m\033[1m"
        + "\n*****USING HUMAN INPUT*****"
        + "\033[0m\033[0m"
    )

log("\033[94m\033[1m" + "\n*****OBJECTIVE*****\n" + "\033[0m\033[0m")
log(f"{OBJECTIVE}")

# Configure OpenAI
openai.api_key = OPENAI_API_KEY

# Task storage supporting only a single instance of BabyAGI
class SingleTaskListStorage:
    def __init__(self, task_list: deque):
        self.tasks = task_list

    def append(self, task: Dict):
        self.tasks.append(task)

    def appendleft(self, task: Dict):
        self.tasks.appendleft(task)

    def replace(self, task_list: deque):
        self.tasks = task_list

    def reference(self, index: int):
        return self.tasks[index]

    def pop(self):
        return self.tasks.pop()

    def popleft(self):
        return self.tasks.popleft()

    def is_empty(self):
        return False if self.tasks else True

    def get_tasks(self):
        return self.tasks

# Task list
temp_task_list = load_data(TASK_LIST_FILE) #deque([])
temp_executed_task_list = load_data(EXECUTED_TASK_LIST_FILE) #deque([])

# Initialize tasks storage
tasks_storage = SingleTaskListStorage(temp_task_list)
executed_tasks_storage = SingleTaskListStorage(temp_executed_task_list)
if COOPERATIVE_MODE in ['l', 'local']:
    if can_import("extensions.ray_tasks"):
        import sys
        from pathlib import Path

        sys.path.append(str(Path(__file__).resolve().parent))
        from extensions.ray_tasks import CooperativeTaskListStorage

        tasks_storage = CooperativeTaskListStorage(OBJECTIVE, temp_task_list)
        log("\nReplacing tasks storage: " + "\033[93m\033[1m" + "Ray" + "\033[0m\033[0m")
        executed_tasks_storage = CooperativeTaskListStorage(OBJECTIVE, temp_executed_task_list)
        log("\nReplacing executed tasks storage: " + "\033[93m\033[1m" + "Ray" + "\033[0m\033[0m")
elif COOPERATIVE_MODE in ['d', 'distributed']:
    pass


if tasks_storage.is_empty() or JOIN_EXISTING_OBJECTIVE:
    log("\033[93m\033[1m" + "\nInitial task:" + "\033[0m\033[0m" + f" {INITIAL_TASK}")
else:
    log("\033[93m\033[1m" + f"\nContinue task" + "\033[0m\033[0m")

log("\n")

def limit_tokens_from_string(string: str, model: str, limit: int) -> str:
    """Limits the string to a number of tokens (estimated)."""

    try:
        encoding = tiktoken.encoding_for_model(model)
    except:
        encoding = tiktoken.encoding_for_model('gpt2')  # Fallback for others.

    encoded = encoding.encode(string)

    return encoding.decode(encoded[:limit])


def openai_call(
    prompt: str,
    model: str = LLM_MODEL,
    temperature: float = OPENAI_TEMPERATURE,
    max_tokens: int = MAX_TOKEN,
):
    while True:
        try:
            if model.lower().startswith("llama"):
                result = llm(prompt[:CTX_MAX],
                             stop=["### Human"],
                             echo=False,
                             temperature=0.2,
                             top_k=40,
                             top_p=0.95,
                             repeat_penalty=1.05,
                             max_tokens=200)
                # log('\n*****RESULT JSON DUMP*****\n')
                # log(json.dumps(result))
                # log('\n')
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
                # Use 8000 instead of the real limit (8194) to give a bit of wiggle room for the encoding of roles.
                # TODO: different limits for different models.

                trimmed_prompt = limit_tokens_from_string(prompt, model, 8000 - max_tokens)

                # Use chat completion API
                messages = [{"role": "system", "content": trimmed_prompt}]
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
            log(
                "   *** The OpenAI API rate limit has been exceeded. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.Timeout:
            log(
                "   *** OpenAI API timeout occurred. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIError:
            log(
                "   *** OpenAI API error occurred. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.APIConnectionError:
            log(
                "   *** OpenAI API connection error occurred. Check your network settings, proxy configuration, SSL certificates, or firewall rules. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.InvalidRequestError:
            log(
                "   *** OpenAI API invalid request. Check the documentation for the specific API method you are calling and make sure you are sending valid and complete parameters. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        except openai.error.ServiceUnavailableError:
            log(
                "   *** OpenAI API service unavailable. Waiting 10 seconds and trying again. ***"
            )
            time.sleep(10)  # Wait 10 seconds and try again
        else:
            break

def task_creation_agent(
        objective: str, result: str, task_description: str, task_list: deque, executed_task_list: deque
):
    prompt = f"""You are an AI that manages tasks to achieve the desired "{objective}" based on the results of the last plan you created. Remove the tasks you've executed and create new tasks if necessary. Please make the tasks you generate executable in a terminal with a single command, if possible. If that's difficult, generate planned tasks with reduced granularity.

Afterwards, organize the tasks, remove any unnecessary tasks for the objective, and output them as a JSON array following the example below. Please never output anything other than a JSON array.

# Example of JSON array output"""
    prompt += """
[
    {
        "type": "command",
        "content": "echo 'import os\\n# HOW TO USE*\\n# 1. Fork this into a private Repl\\n# 2. Add your OpenAI API Key and Pinecone API Key\\n# 4. Update the OBJECTIVE variable\\n# 5. Press \\"Run\\" at the top.\\n# NOTE: the first time you run, it will initiate the table first - which may take a few minutes, you'\\\\''ll be waiting at the initial OBJECTIVE phase. If it fails, try again.)\\n#\\n# WARNING: THIS CODE WILL KEEP RUNNING UNTIL YOU STOP IT. BE MINDFUL OF OPENAI API BILLS. DELETE PINECONE INDEX AFTER USE.\\n\\nimport subprocess\\nimport openai\\n#import pinecone\\nimport time\\nimport json\\nfrom collections import deque\\nfrom typing import Dict, List\\n\\n#Set API Keys\\nOPENAI_API_KEY = os.environ['\\\\''OPEN_API_KEY'\\\\'']\\n#PINECONE_API_KEY = os.environ['\\\\''PINECONE_API_KEY'\\\\'']\\n#PINECONE_ENVIRONMENT = os.environ['\\\\''PINECONE_ENVIRONMENT'\\\\''] #Pinecone Environment (eg. \\"us-east1-gcp\\")\\n\\n#Set Variables\\nYOUR_TABLE_NAME = \\"test-table\\"\\nOBJECTIVE = \\"Implement a game of Minesweeper in python and run it in python.\\"\\nYOUR_FIRST_TASK = \\"Develop a task list.\\"\\n\\nMODEL = \\"gpt-4\\"\\nMAX_TOKEN = 7000\\n\\n#Print OBJECTIVE\\nprint(\\"\\\\033[96m\\\\033[1m\\" + \\"OBJECTIVE\\\\n\\\\n\\" + \\"\\\\033[0m\\\\033[0m\\")\\nprint(OBJECTIVE + \\"\\\\n\\\\n\\")\\n\\n# Configure OpenAI and Pinecone\\nopenai.api_key = OPENAI_API_KEY\\n#pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)\\n\\n# Create Pinecone index\\n#table_name = YOUR_TABLE_NAME' > ./output/sample.py"
    },
    {
        "type": "plan",
        "content": "Develop a task list."
    },
    {
        "type": "command",
        "content": "cd /dir1/dir2/"
    },
    {
        "type": "command",
        "content": "mkdir ./dir3/dir4"
    }
]"""
    prompt += f"""

The following is the execution result of the last planned task.

# Last executed planned task
{task_description}

# Result of the last executed planned task.
{result}

# List of most recently executed command results
{json.dumps(list(executed_task_list))}

# Uncompleted tasks
{json.dumps(list(task_list))}"""

    prompt = prompt[:MAX_STRING_LENGTH]
    prompt += """

# Absolute Rule
Please never output anything other than a JSON array."""

    log("\033[34m\033[1m" + "[[Prompt]]" + "\033[0m\033[0m" + "\n\n" + prompt +
        "\n\n")
    jsonValue = openai_call(prompt)
    log("\033[31m\033[1m" + "[[Response]]" + "\033[0m\033[0m" + "\n\n" +
        jsonValue + "\n\n")
    try:
        return json.loads(jsonValue)
    except Exception as error:
        log("json parse error:")
        log(error)
        log("\nRetry\n\n")
        return task_creation_agent(objective, result, task_description, task_list, executed_task_list)

def check_completion_agent(
        objective: str, result: str, task_description: str, task_list: deque, executed_task_list: deque
):
    prompt = f"""You are an AI that checks whether the "{objective}" has been achieved based on the results, and if not, manages the remaining tasks. Please generate tasks that can be executed in a terminal with one command as much as possible when necessary. If that is difficult, generate planned tasks with reduced granularity.

If the objective is achieved based on the results, output only the string "Complete" instead of an array. In that case, never output anything other than "Complete".

If the objective is not achieved based on the results, remove the executed tasks, and create new tasks if needed. Then, organize the tasks, delete unnecessary tasks for the objective, and output only a JSON array referring to the example below. In that case, never output anything other than the JSON array.

# Example of JSON array output"""
    prompt += """
[
    {
        "type": "command",
        "content": "echo 'import os\\n# HOW TO USE*\\n# 1. Fork this into a private Repl\\n# 2. Add your OpenAI API Key and Pinecone API Key\\n# 4. Update the OBJECTIVE variable\\n# 5. Press \\"Run\\" at the top.\\n# NOTE: the first time you run, it will initiate the table first - which may take a few minutes, you'\\\\''ll be waiting at the initial OBJECTIVE phase. If it fails, try again.)\\n#\\n# WARNING: THIS CODE WILL KEEP RUNNING UNTIL YOU STOP IT. BE MINDFUL OF OPENAI API BILLS. DELETE PINECONE INDEX AFTER USE.\\n\\nimport subprocess\\nimport openai\\n#import pinecone\\nimport time\\nimport json\\nfrom collections import deque\\nfrom typing import Dict, List\\n\\n#Set API Keys\\nOPENAI_API_KEY = os.environ['\\\\''OPEN_API_KEY'\\\\'']\\n#PINECONE_API_KEY = os.environ['\\\\''PINECONE_API_KEY'\\\\'']\\n#PINECONE_ENVIRONMENT = os.environ['\\\\''PINECONE_ENVIRONMENT'\\\\''] #Pinecone Environment (eg. \\"us-east1-gcp\\")\\n\\n#Set Variables\\nYOUR_TABLE_NAME = \\"test-table\\"\\nOBJECTIVE = \\"Implement a game of Minesweeper in python and run it in python.\\"\\nYOUR_FIRST_TASK = \\"Develop a task list.\\"\\n\\nMODEL = \\"gpt-4\\"\\nMAX_TOKEN = 7000\\n\\n#Print OBJECTIVE\\nprint(\\"\\\\033[96m\\\\033[1m\\" + \\"OBJECTIVE\\\\n\\\\n\\" + \\"\\\\033[0m\\\\033[0m\\")\\nprint(OBJECTIVE + \\"\\\\n\\\\n\\")\\n\\n# Configure OpenAI and Pinecone\\nopenai.api_key = OPENAI_API_KEY\\n#pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENVIRONMENT)\\n\\n# Create Pinecone index\\n#table_name = YOUR_TABLE_NAME' > ./output/sample.py"
    },
    {
        "type": "plan",
        "content": "Develop a task list."
    },
    {
        "type": "command",
        "content": "cd /dir1/dir2/"
    },
    {
        "type": "command",
        "content": "mkdir ./dir3/dir4"
    }
]"""
    prompt += f"""          

Below is the result of the last execution.

# Command executed most recently
{task_description}

# Result of last command executed
{result}

# List of most recently executed command results
{json.dumps(list(executed_task_list))}

# Uncompleted tasks
{json.dumps(list(task_list))}"""

    prompt = prompt[:MAX_STRING_LENGTH]
    prompt += """

# Absolute Rule
If the output is anything other than "Complete", please never output anything other than a JSON array."""

    log("\033[34m\033[1m" + "[[Prompt]]" + "\033[0m\033[0m" + "\n\n" + prompt +
        "\n\n")
    jsonValue = openai_call(prompt)
    log("\033[31m\033[1m" + "[[Response]]" + "\033[0m\033[0m" + "\n\n" +
        jsonValue + "\n\n")
    if jsonValue == "Complete":
        return jsonValue
    try:
        return json.loads(jsonValue)
    except Exception as error:
        log("json parse error:")
        log(error)
        log("\nRetry\n\n")
        return check_completion_agent(objective, result, task_description, task_list, executed_task_list)

def plan_agent(objective: str, task: str,
               executed_task_list: deque) -> str:
  #context = context_agent(index=YOUR_TABLE_NAME, query=objective, n=5)
    prompt = f"""You are a Lead Engineer.
You will perform one task based on the following objectives

# OBJECTIVE
{objective}

# Task to be performed.
{task}

# List of most recently executed command results
{json.dumps(list(executed_task_list))}"""

    prompt = prompt[:MAX_STRING_LENGTH]
    log("\033[34m\033[1m" + "[[Prompt]]" + "\033[0m\033[0m" + "\n\n" + prompt +
        "\n\n")
    result = openai_call(prompt)
    log("\033[31m\033[1m" + "[[Response]]" + "\033[0m\033[0m" + "\n\n" +
        result + "\n\n")
    return result

# Execute a task based on the objective and five previous tasks
def execution_command(objective: str, command: str, task_list: deque,
                      executed_task_list: deque) -> str:
    #[Test]
    #command = "export PATH=$PATH:$PWD/flutter/bin"

    #log("saburo:")
    # output environment variables
    #for key, value in os.environ.items():
    #    log(f"{key}: {value}")

    # After the subprocess completes, read the dumped environment variables
    if os.path.isfile(ENV_DUMP_FILE):
        with open(ENV_DUMP_FILE, "r") as env_file:
            for line in env_file:
                name, _, value = line.partition("=")
                #log(f"new environment:{value.strip()}")
                os.environ[name] = value.strip()  # Set the environment variable in the parent process
                #log(f"set environment:{os.environ[name]}")

    current_dir = "."
    if os.path.isfile(PWD_FILE):
        with open(PWD_FILE, "r") as pwd_file:
            current_dir = pwd_file.read().strip()

    log(f"current_dir:\n{current_dir}\n")

    log("\033[33m\033[1m" + "[[Input]]" + "\033[0m\033[0m" + "\n\n" + command +
        "\n")

    # Add an extra command to dump environment variables to a file
    command_to_execute = f"cd {current_dir}; {command}; echo $? > /tmp/cmd_exit_status; pwd > {PWD_FILE}; env > {ENV_DUMP_FILE}"

    pty_master, slave = pty.openpty()
    process = subprocess.Popen(command_to_execute,
                             stdin=slave,
                             stdout=slave,
                             stderr=slave,
                             shell=True,
                             text=True,
                             bufsize=1,
                             env=os.environ)
    os.close(slave)

    std_blocks = []

    while process.poll() is None:

        # Check for output with a timeout of some seconds
        reads, _, _ = select.select([pty_master], [], [], 60)
        if reads:
            for read in reads:
                try:
                    output_block = os.read(read, 1024).decode()
                except OSError:
                    # Break the loop if OSError occurs
                    break

                if output_block:
                    print(output_block, end="")
                    std_blocks.append(output_block)
        else:
            if USER_INPUT_LLM:
                # Concatenate the output and split it by lines
                stdout_lines = "".join(std_blocks).splitlines()

                # No output received within 5 seconds, call the check_wating_for_response function with the last 3 lines or the entire content
                lastlines = stdout_lines[-3:] if len(stdout_lines) >= 3 else stdout_lines
                lastlines = "\n".join(lastlines)
                input = user_input_for_waiting(objective, lastlines, command,
                                         "".join(std_blocks), task_list,
                                         executed_task_list)
                if input == 'BabyCommandAGI: Complete':
                    return input
                elif input == 'BabyCommandAGI: Interruption':
                    break
                elif input == 'BabyCommandAGI: Continue':
                    pass
                else:
                    input += '\n'
                    os.write(pty_master, input.encode())

    os.close(pty_master)
    out = "".join(std_blocks)

    with open("/tmp/cmd_exit_status", "r") as status_file:
        cmd_exit_status = int(status_file.read().strip())

    result = f"The Return Code for the command is {cmd_exit_status}:\n{out}"

    log("\n" + "\033[33m\033[1m" + "[[Output]]" + "\033[0m\033[0m" + "\n\n" +
        result + "\n\n")
    
    return result

def user_input_for_waiting(objective: str, lastlines: str, command: str,
                           all_output_for_command: str, task_list: deque,
                           executed_task_list: deque):
    prompt = f"""You are an expert in shell commands to achieve the "{objective}".
Based on the information below, if the objective has been achieved, please output only 'BabyCommandAGI: Complete'.
Based on the information below, if the objective cannot be achieved and it seems that the objective can be achieved by inputting while waiting for the user's input, please output only the input content for the waiting input content to achieve the objective.
Based on the information below, if the objective cannot be achieved and it seems better to interrupt the execution of the command to achieve the objective, please output only 'BabyCommandAGI: Interruption'.
Otherwise, please output only 'BabyCommandAGI: Continue'.

# All output content so far for the command being executed
{all_output_for_command}

# List of most recently executed command results
{json.dumps(list(executed_task_list))}

# Uncompleted tasks
{json.dumps(list(task_list))}"""

    prompt = prompt[:MAX_STRING_LENGTH]
    prompt += f"""

# Command being executed
{command}

# The last 3 lines of the terminal
{lastlines}

# Absolute rule
Please output only the following relevant content. Never output anything else.

If the objective has been achieved: 'BabyCommandAGI: Complete'
If the objective cannot be achieved and it seems that the objective can be achieved by inputting while waiting for the user's input: Input content for the waiting input content to achieve the objective
If the objective cannot be achieved and it seems better to interrupt the execution of the command to achieve the objective: 'BabyCommandAGI: Interruption'
In cases other than the above: 'BabyCommandAGI: Continue'"""

    log("\n\n")
    log("\033[34m\033[1m" + "[[Prompt]]" + "\033[0m\033[0m" + "\n\n" + prompt +
        "\n\n")
    result = openai_call(prompt)
    log("\033[31m\033[1m" + "[[Response]]" + "\033[0m\033[0m" + "\n\n" +
        result + "\n\n")
    return result

# Add the initial task if starting new objective
if tasks_storage.is_empty() or JOIN_EXISTING_OBJECTIVE:
    initial_task = {"type": "plan", "content": INITIAL_TASK}
    tasks_storage.append(initial_task)

def main():
    loop = True
    new_tasks_list = []
    while loop:
        # As long as there are tasks in the storage...
        if tasks_storage:
            # Step 1: Pull the first task
            task = tasks_storage.popleft()
            log("\033[92m\033[1m" + "*****NEXT TASK*****\n\n" + "\033[0m\033[0m")
            log(str(task['type']) + ": " + task['content'] + "\n\n")

            # Check executable command
            if task['type'] == "command":
                log("\033[33m\033[1m" + "*****EXCUTE COMMAND TASK*****\n\n" +
                "\033[0m\033[0m")

                while True:

                    result = execution_command(OBJECTIVE, task['content'], tasks_storage.get_tasks(),
                                    executed_tasks_storage.get_tasks())
                    

                    # Step 2: Enrich result and store
                    enriched_result = {"command": task['content'], "result": result}
                    executed_tasks_storage.appendleft(enriched_result)
                    save_data(executed_tasks_storage.get_tasks(), EXECUTED_TASK_LIST_FILE)
                    

                    # Keep only the most recent 30 tasks
                    if len(executed_tasks_storage.get_tasks()) > 30:
                        executed_tasks_storage.pop()

                    if result != "The Return Code for the command is 0:\n":
                        break

                    if tasks_storage.is_empty():
                        break
                    else:
                        next_task = tasks_storage.reference(0)
                        if next_task['type'] == "command":
                            task = tasks_storage.popleft()
                        else:
                            break

                log("\033[32m\033[1m" + "*****TASK RESULT*****\n\n" + "\033[0m\033[0m")

                # Step 3: Create new tasks and reprioritize task list
                new_tasks_list = check_completion_agent(OBJECTIVE, result,
                                                     task['content'], tasks_storage.get_tasks(),
                                                     executed_tasks_storage.get_tasks())
                
                if new_tasks_list == "Complete":
                    log("\033[92m\033[1m" + "*****TASK COMPLETE*****\n\n" +
                        "\033[0m\033[0m")
                    break

            else:
                log("\033[33m\033[1m" + "*****PLAN TASK*****\n\n" + "\033[0m\033[0m")
                result = plan_agent(OBJECTIVE, task['content'], executed_tasks_storage.get_tasks())

                # Send to execution function to complete the task based on the context
                log("\033[32m\033[1m" + "*****TASK RESULT*****\n\n" + "\033[0m\033[0m")

                # Step 3: Create new tasks and reprioritize task list
                new_tasks_list = task_creation_agent(OBJECTIVE, result, task['content'],
                                              tasks_storage.get_tasks(), executed_tasks_storage.get_tasks())
                
        tasks_storage.replace(deque(new_tasks_list))
        save_data(tasks_storage.get_tasks(), TASK_LIST_FILE)
        
        time.sleep(1)

if __name__ == "__main__":
    main()
