# Task-Driven Autonomous Agent UI 👶💻

Task-Driven Autonomous Agent (`TDAA`) leverages [OpenAI’s](https://platform.openai.com/docs/models) GPT language models, [Pinecone](https://www.pinecone.io/) vector search, and the [LangChain framework](https://github.com/hwchase17/langchain) to perform a wide range of tasks across diverse domains. This application is an implementation of the [babyAGI engine](https://github.com/yoheinakajima/babyagi), (proposed by [Yohei Nakajima](https://yoheinakajima.com/)) a system capable of completing tasks, generating new tasks based on completed results, and prioritizing tasks in real-time.

The system uses:

- `GPT-3.5` (you can specify other models if you want) to perform various tasks based on the given context.
- `Pinecone` to store and retrieve task-related data, such as task descriptions, constraints, and results.
- All is integrated with the `LangChain` framework to enhance the agent's capabilities, particularly in task completion and agent-based decision-making processes.

Overall, the agent maintains a task list, represented by a double-ended queue data structure, to manage and prioritize tasks. The system autonomously creates new tasks based on completed results and reprioritized the task list accordingly. The result is a powerful optimizer capable of solving many kinds of complex tasks.

This application is a simple dash app that creates a user interface for the `TDAA`. All credits for the code implementation goes to [babyagi](https://github.com/yoheinakajima/babyagi), a.k.a. [Yohei Nakajima](https://github.com/yoheinakajima), how made a clean, simple, and easy to replicate implementation.

In this version, the controller can set how many rounds the `TDAA` agent will optimize its tasks. Also, the memory `deque` list was set so that the agent can optimize more than one objective in a single session, i.e., after completing the specified round, you can set a new objective/task, and the previous task won't affect the new rounds. If you wish to extend the memory of the `TDAA`, just add more rounds.

> WARNING: Long/Infinite rounds of querying OpenAI's and Pinecone APIs can become expensive...

## Controls ⚙️

- `Rounds`: Number of times the TDAA repeats an execution loop (completing the task, generating new tasks, prioritizing tasks).
- `Objective`: The goal you are trying to attain.
- `First Task`: An initial task to get things started.

## Requirements 🛠️

```bash
dash
openai
pinecone-client
dash-bootstrap-components
```

> Note: You will also need to have an OpenAI API key, and a Pinecone API key as well.
