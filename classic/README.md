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

Finally, the script uses Pinecone to store and retrieve task results for context. The script creates a Pinecone index based on the table name specified in YOUR_TABLE_NAME variable. Pinecone is then used to store the results of the task in the index, along with the task name and any additional metadata.

# How to Use
To use the script, you will need to follow these steps:

1. Install the required packages: `pip install -r requirements.txt`
2. Set your OpenAI and Pinecone API keys in the OPENAI_API_KEY and PINECONE_API_KEY variables.
3. Set the Pinecone environment in the PINECONE_ENVIRONMENT variable.
4. Set the name of the table where the task results will be stored in the YOUR_TABLE_NAME variable.
5. Set the objective of the task management system in the OBJECTIVE variable.
6. Set the first task of the system in the YOUR_FIRST_TASK variable.
7. Run the script.

# API mode (via [e2b](https://www.e2b.dev/))
To start the server run:
```bash
python api.py
```

and then you can call the API using either the following commands:

To **create a task** run:
```bash
curl --request POST \
  --url http://localhost:8000/agent/tasks \
  --header 'Content-Type: application/json' \
  --data '{
	"input": "Find the Answer to the Ultimate Question of Life, the Universe, and Everything."
}'
```

You will get a response like this:
```json
{"input":"Find the Answer to the Ultimate Question of Life, the Universe, and Everything.","task_id":"d2c4e543-ae08-4a97-9ac5-5f9a4459cb19","artifacts":[]}
```

Then to **execute one step of the task** copy the `task_id` you got from the previous request and run:

```bash
curl --request POST \
  --url http://localhost:8000/agent/tasks/<task-id>/steps
```

or you can use [Python client library](https://github.com/e2b-dev/agent-protocol/tree/main/agent_client/python):

```python
from agent_protocol_client import AgentApi, ApiClient, TaskRequestBody

...

prompt = "Find the Answer to the Ultimate Question of Life, the Universe, and Everything."

async with ApiClient() as api_client:
    # Create an instance of the API class
    api_instance = AgentApi(api_client)
    task_request_body = TaskRequestBody(input=prompt)

    task = await api_instance.create_agent_task(
        task_request_body=task_request_body
    )
    task_id = task.task_id
    response = await api_instance.execute_agent_task_step(task_id=task_id)

...

```


# Warning
This script is designed to be run continuously as part of a task management system. Running this script continuously can result in high API usage, so please use it responsibly. Additionally, the script requires the OpenAI and Pinecone APIs to be set up correctly, so make sure you have set up the APIs before running the script.

#Backstory
BabyAGI is a paired-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023) shared on Twitter. This version is down to 140 lines: 13 comments, 22 blank, 105 code. The name of the repo came up in the reaction to the original autonomous agent - the author does not mean to imply that this is AGI.

Made with love by [@yoheinakajima](https://twitter.com/yoheinakajima), who happens to be a VC - so if you use this build a startup, ping him!
