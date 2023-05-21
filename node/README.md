# node-chroma babyagi

# Objective

This Node script is an example of an AI-powered task management system. The system uses OpenAI and Chroma APIs to create, prioritize, and execute tasks. The main idea behind this system is that it creates tasks based on the result of previous tasks and a predefined objective. The script then uses OpenAI's natural language processing (NLP) capabilities to create new tasks based on the objective, and Chroma to store and retrieve task results for context. This is a paired-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023).

This README will cover the following:

- How the script works

- How to use the script
- Warning about running the script continuously

# How It Works

The script works by running an infinite loop that does the following steps:

1. Pulls the first task from the task list.
2. Sends the task to the execution agent, which uses OpenAI's API to complete the task based on the context.
3. Enriches the result and stores it in [Chroma](docs.trychroma.com).
4. Creates new tasks and reprioritizes the task list based on the objective and the result of the previous task.
   The execution_agent() function is where the OpenAI API is used. It takes two parameters: the objective and the task. It then sends a prompt to OpenAI's API, which returns the result of the task. The prompt consists of a description of the AI system's task, the objective, and the task itself. The result is then returned as a string.

The task_creation_agent() function is where OpenAI's API is used to create new tasks based on the objective and the result of the previous task. The function takes four parameters: the objective, the result of the previous task, the task description, and the current task list. It then sends a prompt to OpenAI's API, which returns a list of new tasks as strings. The function then returns the new tasks as a list of dictionaries, where each dictionary contains the name of the task.

The prioritization_agent() function is where OpenAI's API is used to reprioritize the task list. The function takes one parameter, the ID of the current task. It sends a prompt to OpenAI's API, which returns the reprioritized task list as a numbered list.

Finally, the script uses Chroma to store and retrieve task results for context. The script creates a Chroma collection based on the table name specified in the TABLE_NAME variable. Chroma is then used to store the results of the task in the collection, along with the task name and any additional metadata.

# How to Use

To use the script, you will need to follow these steps:

1. Install the required packages: `npm install`
2. Install chroma in this directory (based on the Chroma [docs](https://docs.trychroma.com/getting-started)) :
   ```
   git clone git@github.com:chroma-core/chroma.git
   ```
3. Make sure Docker is running on your machine
4. Set your OpenAI and in the OPENAI_API_KEY variables.
5. Set your OpenAI API key in the OPENAI_API_KEY and OPENAPI_API_MODEL variables.
6. Set the name of the table where the task results will be stored in the TABLE_NAME variable.
7. Run the script with 'npm run babyagi'. This will handle 'docker compose up.'
8. Provide the objective of the task management system when prompted.
9. Provide the objective of the task management system when prompted.

# Warning

This script is designed to be run continuously as part of a task management system. Running this script continuously can result in high API usage, so please use it responsibly. Additionally, the script requires the OpenAI and Pinecone APIs to be set up correctly, so make sure you have set up the APIs before running the script.

# Backstory

BabyAGI is a paired-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023) shared on Twitter. This version is down to 140 lines: 13 comments, 22 blank, 105 code. The name of the repo came up in the reaction to the original autonomous agent - the author does not mean to imply that this is AGI.

# TODO

- [x] Implement BabyAGI in nodex
- [x] Switch Pinecome to Chroma
- [ ] Add LLaMA support
- [ ] Allow users to modify model params
- [ ] Support command line args
- [ ] Allow agent to request additional input from user ( could be an interesting strategy to mitigate looping )

Made with love by :

- [@yoheinakajima](https://twitter.com/yoheinakajima) (0->1), who happens to be a VC - so if you use this build a startup, ping him!

Contributions from:

- [@anton](https://twitter.com/atroyn) (pinecone->chroma), who happens to be a founder at [Chroma](https://www.trychroma.com/)
- [@aidanjrauscher](https://twitter.com/aidanjrauscher) (python->node), who happens to be trying to find a job
