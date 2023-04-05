# AI Project Manager

AI Project Manager is an AI-driven system that manages tasks, executes them, generates new tasks, and reprioritizes the task list. It uses OpenAI for natural language understanding, Pinecone for task-result storage, and embeddings for context retrieval.

All credit goes to @yoheinakajima

## Description

AI Project Manager helps you automate the task management process of your projects. It's designed to understand and execute tasks, generate new tasks based on completed tasks, and prioritize tasks according to their importance. The project consists of the following components:

1. AI Assistant
2. Task Manager
3. Main Script

### Features

- Task management with priority
- Automatic task generation based on completed tasks
- Task execution with the help of AI models
- Context retrieval using Pinecone
- Embeddings for tasks and results

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
</pre>


|- README.md
|- .gitignore
|- configs
|   |- config.yaml
|- requirements.txt
|- scripts
|   |- main.py
|- src
    |- __init__.py
    |- agent_manager.py
    |- task_manager.py
    |- utils.py
    |- agents
    |   |- __init__.py
    |   |- base_agent.py
    |   |- context_agent.py
    |   |- execution_agent.py
    |   |- prioritization_agent.py
    |   |- task_creation_agent.py

## Installation & Usage

1. Install the required packages: pip install -r requirements.txt
2. In `configs.yaml` file, set your OpenAI and Pinecone API keys in the `OPENAI_API_KEY` and `PINECONE_API_KEY` variables.
3. Set the Pinecone environment in the `PINECONE_ENVIRONMENT` variable.
4. Set the name of the table where the task results will be stored in the `TABLE_NAME` variable.
5. Set the first task of the system in the `FIRST_TASK` variable.
6. Run the script.

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
