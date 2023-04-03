# babyagi


# Objective
This Python script is an example of an AI-powered task management system. The system uses OpenAI and Pinecone APIs to create, prioritize, and execute tasks. The main idea behind this system is that it creates tasks based on the result of previous tasks and a predefined objective. The script then uses OpenAI's natural language processing (NLP) capabilities to create new tasks based on the objective, and Pinecone to store and retrieve task results for context. This is a paired-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023).

This README will cover the following:

* How the script works 

* How to use the script 
* Warning about running the script continuously
# How It Works
The script works by running an infinite loop that does the following steps:

1. Pulls the first task from the task list.
2. Sends the task to the execution agent, which uses OpenAI's API to complete the task based on the context.
3. Enriches the result and stores it in Pinecone.
4. Creates new tasks and reprioritizes the task list based on the objective and the result of the previous task.
The execution_agent() function is where the OpenAI API is used. It takes two parameters: the objective and the task. It then sends a prompt to OpenAI's API, which returns the result of the task. The prompt consists of a description of the AI system's task, the objective, and the task itself. The result is then returned as a string.

The task_creation_agent() function is where OpenAI's API is used to create new tasks based on the objective and the result of the previous task. The function takes four parameters: the objective, the result of the previous task, the task description, and the current task list. It then sends a prompt to OpenAI's API, which returns a list of new tasks as strings. The function then returns the new tasks as a list of dictionaries, where each dictionary contains the name of the task.

The prioritization_agent() function is where OpenAI's API is used to reprioritize the task list. The function takes one parameter, the ID of the current task. It sends a prompt to OpenAI's API, which returns the reprioritized task list as a numbered list.

Finally, the script uses Pinecone to store and retrieve task results for context. The script creates a Pinecone index based on the table name specified in PINECONE_TABLE variable. Pinecone is then used to store the results of the task in the index, along with the task name and any additional metadata.

# How to Use
To use the script, you will need to follow these steps:

1. Create a virtual environment and activate it. To do this on Mac or Linux, run the following commands:
```bash
python3 -m venv venv
source venv/bin/activate
```
To do this on Windows, run the following commands:
```bash
python3 -m venv venv
venv\Scripts\activate
```
2. Install the required packages: 
```bash
pip install -r requirements.txt
```
3. Copy the .env.example file to .env and fill in the variables.
4. Run the script using the following command:
```bash
python babyagi.py
```
5. Select the OpenAI model you want to use. GPT-3 (text-davinci-003) returns the fastest results. Additionally, you will need GPT-4 API access to use the GPT-4 model.
6. Enter the Objective you want babyagi to work towards. The objective should be a short description of what you want babyagi to do. For example, if you want babyagi to solve world peace, the objective could be "Solve World Peace."
7. Enter the task description. The task description should be a short description of the task you want babyagi to complete to work towards the objective. For example, if you want babyagi to solve world peace, the task description could be "Create 3 tasks to solve world peace"
8. Watch babyagi work towards the objective!

Note: This script will run continuously until you stop it. To stop the script, enter 'kill' inside the console.

# Warning
This script is designed to be run continuously as part of a task management system. Running this script continuously can result in high API usage, so please use it responsibly. Additionally, the script requires the OpenAI and Pinecone APIs to be set up correctly, so make sure you have set up the APIs before running the script.

#Backstory
BabyAGI is a paired-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023) shared on Twitter. This version is down to 140 lines: 13 comments, 22 blank, 105 code. The name of the repo came up in the reaction to the original autonomous agent - the author does not mean to imply that this is AGI.

Made with love by [@yoheinakajima](https://twitter.com/yoheinakajima), who happens to be a VC - so if you use this build a startup, ping him!
