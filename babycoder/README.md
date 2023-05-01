# Babycoder: Recipe for using BabyAgi to write code

Babycoder is a work in progress AI system that is able to write code for small programs given a simple objective. As a part of the BabyAgi system, Babycoder's goal is to lay the foundation for creating increasingly powerful AI agents capable of managing larger and more complex projects.

## Objective

The primary objective of Babycoder is to provide a recipe for developing AI agent systems capable of writing and editing code. By starting with a simple system and iterating on it, Babycoder aims to improve over time and eventually handle more extensive projects.

## How It Works

Babycoder's task management system consists of several AI agents working together to create, prioritize, and execute tasks based on a predefined objective and the results of previous tasks. The process consists of the following steps:

1. **Task Definition**: Four task agents define tasks in a JSON list, which includes all tasks to be executed by the system.

2. **Agent Assignment**: For each task, two agents collaborate to determine the agent responsible for executing the task. The possible executor agents are:
    - `command_executor_agent`
    - `code_writer_agent`
    - `code_refactor_agent`

3. **File Management**: The `files_management_agent` scans files in the project directory to determine which files or folders will be used by the executor agents to accomplish their tasks.

4. **Task Execution**: The executor agents perform their assigned tasks using the following capabilities:
    - The `command_executor_agent` runs OS commands, such as installing dependencies or creating files and folders.
    - The `code_writer_agent` writes new code or updates existing code, using embeddings of the current codebase to retrieve relevant code sections and ensure compatibility with other parts of the codebase.
    - The `code_refactor_agent` edits existing code according to the specified task, with the help of a `code_relevance_agent` that analyzes code chunks and identifies the most relevant section for editing.

The code is written to a folder called `playground` in Babycoder's root directory. A folder named `playground_data` is used to save embeddings of the code being written.

## How to use

- Configure BabyAgi by following the instructions in the main README file.
- Navigate to the babycoder directory: `cd babycoder`
- Make a copy of the objective.sample.txt file (`cp objective.sample.txt objective.txt`) and update it to contain the objective of the project you want to create. 
- Finally, from the `./babycoder` directory, run: `python babycoder.py` and watch it write code for you!