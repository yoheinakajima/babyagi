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
2. Copy the .env.example file to .env: `cp .env.example .env`. This is where you will set the following variables.
3. Set your OpenAI and Pinecone API keys in the OPENAI_API_KEY and PINECONE_API_KEY variables.
4. Set the Pinecone environment in the PINECONE_ENVIRONMENT variable.
5. Set the name of the table where the task results will be stored in the TABLE_NAME variable.
6. Set the objective of the task management system in the OBJECTIVE variable. Alternatively you can pass it to the script as a quote argument.
```
./babyagi.py ["<objective>"]
```
7. Set the first task of the system in the FIRST_TASK variable.
8. Run the script.

# Warning
This script is designed to be run continuously as part of a task management system. Running this script continuously can result in high API usage, so please use it responsibly. Additionally, the script requires the OpenAI and Pinecone APIs to be set up correctly, so make sure you have set up the APIs before running the script.

# Contributing

We appreciate any contributions to improve and expand babyagi. Here are some suggestions for areas that need fixing or improvement:

- **Error handling**: Add proper error handling to ensure the script does not crash or stall due to unexpected issues.
- **Code refactoring**: Improve the code structure and organization to enhance readability and maintainability.
- **Task result enrichment**: Currently, the script only enriches the task result with the task name and result. Expand the enrichment process to include more useful metadata and context.
- **Alternative storage options**: Pinecone is used as the vector database in this implementation. Investigate and implement alternative storage options to provide more flexibility for users.
- **Model selection**: The script can switch between GPT-3 and GPT-4, but the process is manual. Implement a more dynamic model selection mechanism to optimize performance and cost.
- **Testing**: Add unit tests and integration tests to ensure the script's reliability and stability.
- **Documentation**: Improve and expand the documentation to provide more clarity and guidance for users.

When contributing, please adhere to the following guidelines:

1. Fork the repository and create a new branch for your feature or fix.
2. Write a clear and concise commit message describing the changes.
3. Create a pull request and provide a detailed description of your changes.

Thank you for your contributions!

# Backstory
BabyAGI is a paired-down version of the original [Task-Driven Autonomous Agent](https://twitter.com/yoheinakajima/status/1640934493489070080?s=20) (Mar 28, 2023) shared on Twitter. This version is down to 140 lines: 13 comments, 22 blank, 105 code. The name of the repo came up in the reaction to the original autonomous agent - the author does not mean to imply that this is AGI.

Made with love by [@yoheinakajima](https://twitter.com/yoheinakajima), who happens to be a VC - so if you use this build a startup, ping him!
