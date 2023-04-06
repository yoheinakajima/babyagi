# Autonomous Collective Decision Making (ACDM)

ACDM wraps around a large language model and a vector database, and serves the begining stages of a digital organization designed to be self-governing, autonomous, and scale-changing. The main intent is to allow agents to collectively manage resources, make decisions, and govern themselves. Design decisions include, but not are limited to autonoumous processes that ensures all agents have an equal say in the direction and management of the organization.

In its current form, it is an AI-driven system that manages tasks, executes them, generates new tasks, and reprioritizes the task list. It uses OpenAI for natural language understanding, Pinecone for task-result storage, and embeddings for context retrieval.

To be depricated at any moment. All credit goes to @OpenAI and @yoheinakajima

## Description

ACDM helps you automate the task management process of your projects. It's designed to understand and execute tasks, generate new tasks based on completed tasks, and prioritize tasks according to their importance. The project consists of the following components:

Task Manager:

* Maintains and organizes a list of tasks
* Provides functionalities to add, remove, and query tasks
* Stores tasks as dictionaries with relevant information

Agents:

* Modular components interacting with Task Manager
* Perform specific actions on tasks
* Designed to be easily interchangeable for flexibility

Agent Types:
* Task Creation Agent: Generates new tasks based on context
* Prioritization Agent: Adjusts task priority within the task list
* Execution Agent: Executes tasks and produces results
* Context Agent: Manages contextual information for task execution

## Visuals

<pre>
+----------------+          +---------------+          +----------------+
| Task Manager   |--------->| AI Assistant  |--------->| Pinecone Index |
+----------------+          +---------------+          +----------------+
        ^                           |
        |                           v
 +--------------+          +-----------------------+
 | Task List    |<---------| Task Creation Agent   |
 +--------------+          +-----------------------+
        ^                           |
        |                           v
 +--------------+          +-----------------------+
 | Prioritization|<--------| Prioritization Agent  |
 +--------------+          +-----------------------+
        ^                           |
        |                           v
 +--------------+          +-----------------------+
 | Execution    |<---------| Execution Agent       |
 +--------------+          +-----------------------+
        ^                           |
        |                           v
 +--------------+          +-----------------------+
 | Context      |<---------| Context Agent         |
 +--------------+          +-----------------------+
</pre>


## Installation & Usage

1. Install the required packages: pip install -r requirements.txt
2. In `configs.yaml` file, set your OpenAI and Pinecone API keys in the `OPENAI_API_KEY` and `PINECONE_API_KEY` variables.
3. Set the Pinecone environment in the `PINECONE_ENVIRONMENT` variable.
4. Set the name of the table where the task results will be stored in the `TABLE_NAME` variable.
5. Set the first task of the system in the `FIRST_TASK` variable.
6. Run the script: python scripts/main.py

## Support

For support, please raise an issue on the project's GitHub repository or contact the maintainers via email.

## Roadmap

_TODO: List planned features, improvements, or fixes for future releases._

## Contributing

Contributions are welcome! Please read the contributing guidelines before submitting a pull request or opening an issue.

## Authors and Acknowledgment

All credit goes to @yoheinakajima. This work is built on BABYAGI project

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Project Status

This project is under active development. If you'd like to become a maintainer or contribute to the project, please get in touch with the current maintainers.
