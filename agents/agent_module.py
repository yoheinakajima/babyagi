from helper import openai_call, save_script_to_file, execute_terminal_command
from validation.validation_module import is_valid_python_script, is_valid_javascript_script, is_valid_css_script, is_valid_terminal_command
from collections import deque
from typing import Dict, List
import re

USE_GPT4 = False


def create_custom_agent(agent_name: str, role: str, prompt: str):
    def custom_agent(task, shared_context):
        task_name = task['task_name']
        task_id = task['task_id']
        response = openai_call(prompt, USE_GPT4, 0.7, 2000)
        if response:
            return response
        else:
            return "No solution generated."

    return custom_agent


def prompt_generator(task, shared_context):
    task_name = task['task_name']
    task_id = task['task_id']
    prompt = (f"You are an AI tasked with completing the following task: {task_name}. "
              f"Here is the context to help you:\n{shared_context}\n"
              f"Generate a prompt that will help another AI complete the task, only returning the prompt. "
              f"Here's your response:\n")
    response = openai_call(prompt, USE_GPT4, 0.7, 2000)
    if response:
        return response
    else:
        return "No prompt generated."


def create_python_developer_agent():
    def python_developer(task, shared_context):
        task_name = task['task_name']
        task_id = task['task_id']
        prompt = (f"You are an AI tasked with completing the following Python task: {task_name}. "
                  f"Here is the context to help you:\n{shared_context}\n"
                  f"Generate a Python script that will accomplish the task. "
                  f"When you are finished, add the line --PYTHON SCRIPT-- followed by the script. "
                  f"Here's your response:\n")
        response = openai_call(prompt, USE_GPT4, 0.7, 2000)
        if is_valid_python_script(response):
            script = response.split('--PYTHON SCRIPT--', 1)[1]
            save_script_to_file(
                script, f"task_{task_id}_{task_name.replace(' ', '_')}.py")
            return "Python task completed: " + task_name
        else:
            return "The generated result does not contain a valid Python script."

    return python_developer


def create_javascript_developer_agent():
    def javascript_developer(task, shared_context):
        task_name = task['task_name']
        task_id = task['task_id']
        prompt = (f"You are an AI tasked with completing the following JavaScript task: {task_name}. "
                  f"Here is the context to help you:\n{shared_context}\n"
                  f"Generate a JavaScript script that will accomplish the task. "
                  f"When you are finished, add the line --JAVASCRIPT SCRIPT-- followed by the script. "
                  f"Here's your response:\n")
        response = openai_call(prompt, USE_GPT4, 0.7, 2000)
        if is_valid_javascript_script(response):
            script = response.split('--JAVASCRIPT SCRIPT--', 1)[1]
            save_script_to_file(
                script, f"task_{task_id}_{task_name.replace(' ', '_')}.js")
            return "JavaScript task completed: " + task_name
        else:
            return "The generated result does not contain a valid JavaScript script."
    return javascript_developer


def create_css_developer_agent():
    def css_developer(task, shared_context):
        task_name = task['task_name']
        task_id = task['task_id']
        prompt = (f"You are an AI tasked with completing the following CSS task: {task_name}. "
                  f"Here is the context to help you:\n{shared_context}\n"
                  f"Generate a CSS script that will accomplish the task. "
                  f"When you are finished, add the line --CSS SCRIPT-- followed by the script. "
                  f"Here's your response:\n")
        response = openai_call(prompt, USE_GPT4, 0.7, 2000)
        if is_valid_css_script(response):
            script = response.split('--CSS SCRIPT--', 1)[1]
            save_script_to_file(
                script, f"task_{task_id}_{task_name.replace(' ', '_')}.css")
            return "CSS task completed: " + task_name
        else:
            return "The generated result does not contain a valid CSS script."
    return css_developer


def create_researcher_agent():
    def researcher(task, shared_context):
        task_name = task['task_name']
        task_id = task['task_id']
        prompt = (f"You are an AI tasked with completing the following task: {task_name}. "
                  f"Here is the context to help you:\n{shared_context}\n"
                  f"Generate a research paper that will help another AI complete the task. "
                  f"Here's your response:\n")
        response = openai_call(prompt, USE_GPT4, 0.7, 2000)
        if response:
            save_script_to_file(
                response, f"task_{task_id}_{task_name.replace(' ', '_')}.txt")
            return "Research task completed: " + task_name
        else:
            return "No research paper generated."
    return researcher


def create_new_agents(response: str) -> List[Dict[str, str]]:
    new_agents = []

    # Regular expression to match new agent format: --NEW AGENT--:AgentName:Role
    agent_pattern = re.compile(r'--NEW AGENT--:(.+?):(.+?)\n')

    # Iterate over all matched agents in the response
    for agent_match in agent_pattern.finditer(response):
        agent_name = agent_match.group(1).strip()
        agent_role = agent_match.group(2).strip()

        new_agents.append({
            'name': agent_name,
            'role': agent_role
        })

    return new_agents


def create_terminal_agent():
    def terminal(task, shared_context):
        task_name = task['task_name']
        task_id = task['task_id']
        prompt = (f"You are an AI tasked with completing the following terminal task: {task_name}. "
                  f"Here is the context to help you:\n{shared_context}\n"
                  f"Generate a terminal command that will accomplish the task. "
                  f"Only return the command, and make sure it is valid. "
                  f"for programs that require user input, use your best judgement. "
                  f"for example, if the program asks for a file name, you can use a hardcoded file name. "
                  f"When you are finished, add the line --TERMINAL COMMAND-- followed by the command. "
                  f"Here's your response:\n")
        response = openai_call(prompt, USE_GPT4, 0.7, 2000)
        if is_valid_terminal_command(response):
            command = response.split('--TERMINAL COMMAND--', 1)[1]
            execute_terminal_command(command)
            return "Terminal task completed: " + task_name
        else:
            return "The generated result does not contain a valid terminal command."
    return terminal


def prioritization_agent(this_task_id: int, task_list: deque, OBJECTIVE: str, gpt_version: str = 'gpt-3'):
    task_names = [t["task_name"] for t in task_list]
    next_task_id = int(this_task_id)+1
    prompt = f"""You are an task prioritization AI tasked with cleaning the formatting of and reprioritizing the following tasks: {task_names}. Consider the ultimate objective of your team:{OBJECTIVE}. Do not remove any tasks. Return the result as a numbered list, like:
    #. First task
    #. Second task
    Start the task list with number {next_task_id}."""
    response = openai_call(prompt, USE_GPT4)
    new_tasks = response.split('\n')
    task_list = deque()
    for task_string in new_tasks:
        task_parts = task_string.strip().split(".", 1)
        if len(task_parts) == 2:
            task_id = task_parts[0].strip()
            task_name = task_parts[1].strip()
            task_list.append({"task_id": task_id, "task_name": task_name})
    return "Task list reprioritized."
