# BabyAGI

> [!NOTE]
> The original BabyAGI from March 2023 introduced task planning as a method for developing autonomous agents. This project has been archived and moved to the [babyagi_archive](https://github.com/yoheinakajima/babyagi_archive) repo (September 2024 snapshot).

> [!CAUTION]
> This is a framework built by Yohei who has never held a job as a developer. The purpose of this repo is to share ideas and spark discussion and for experienced devs to play with. Not meant for production use. Use with cautioun.

---

This newest BabyAGI is an experimental framework for a self-building autonomous agent. Earlier efforts to expand BabyAGI have made it clear that the optimal way to build a general autonomous agent is to build the simplest thing that can build itself.

Check out [this introductory X/Twitter thread](https://x.com/yoheinakajima/status/1840678823681282228) for a simple overview.

The core is a new function framework (**functionz**) for storing, managing, and executing functions from a database. It offers a graph-based structure for tracking imports, dependent functions, and authentication secrets, with automatic loading and comprehensive logging capabilities. Additionally, it comes with a dashboard for managing functions, running updates, and viewing logs.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Usage](#basic-usage)
- [Function Metadata](#function-metadata)
- [Function Loading](#function-loading)
- [Key Dependencies](#key-dependencies)
- [Execution Environment](#execution-environment)
  - [Log](#log)
- [Dashboard](#dashboard)
- [Pre-loaded Functions](#pre-loaded-functions)
- [Future/Draft Features](#futuredraft-features)
- [API Reference](#api-reference)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

To quickly check out the dashboard and see how it works:

1. **Install BabyAGI:**

    ```bash
    pip install babyagi
    ```

2. **Import BabyAGI and load the dashboard:**

    ```python
    import babyagi

    if __name__ == "__main__":
        app = babyagi.create_app('/dashboard')
        app.run(host='0.0.0.0', port=8080)
    ```

3. **Navigate to the dashboard:**

    Open your browser and go to `http://localhost:8080/dashboard` to access the BabyAGI dashboard.
    
## Basic Usage

Start by importing `babyagi` and registering your functions. Here's how to register two functions, where one depends on the other:

```python
import babyagi

# Register a simple function
@babyagi.register_function()
def world():
    return "world"

# Register a function that depends on 'world'
@babyagi.register_function(dependencies=["world"])
def hello_world():
    x = world()
    return f"Hello {x}!"

# Execute the function
print(babyagi.hello_world())  # Output: Hello world!

if __name__ == "__main__":
    app = babyagi.create_app('/dashboard')
    app.run(host='0.0.0.0', port=8080)
```

## Function Metadata

Functions can be registered with metadata to enhance their capabilities and manage their relationships. Here's a more comprehensive example of function metadata, showing logical usage of all fields:

```python
import babyagi

@babyagi.register_function(
    imports=["math"],
    dependencies=["circle_area"],
    key_dependencies=["openai_api_key"],
    metadata={
        "description": "Calculates the volume of a cylinder using the circle_area function."
    }
)
def cylinder_volume(radius, height):
    import math
    area = circle_area(radius)
    return area * height
```

**Available Metadata Fields:**

- `imports`: List of external libraries the function depends on.
- `dependencies`: List of other functions this function depends on.
- `key_dependencies`: List of secret keys required by the function.
- `metadata["description"]`: A description of what the function does.

## Function Loading

In addition to using `register_function`, you can use `load_function` to load plugins or draft packs of functions. BabyAGI comes with built-in function packs, or you can load your own packs by pointing to the file path.

You can find available function packs in `babyagi/functionz/packs`.

**Loading Custom Function Packs:**

```python
import babyagi

# Load your custom function pack
babyagi.load_functions("path/to/your/custom_functions.py")
```

This approach makes function building and management easier by organizing related functions into packs.

## Key Dependencies

### Web search and page fetching

BabyAGI preloads `parallel_search` and `parallel_fetch`, backed by
[Parallel Search MCP](https://docs.parallel.ai/integrations/mcp/search-mcp).
Search uses Fast mode with no account or search API key. From this checkout,
install the runtime requirements and package with Python 3.10 or 3.11:

```bash
python -m pip install -r requirements.txt
python -m pip install --no-deps .
```

Omit `available_function_names` to give the function-calling chat these tools:

```python
import babyagi

# Configure your model provider as usual, for example OPENAI_API_KEY.
history = [
    {"role": "user", "message": "Find recent Python release news and cite the sources."}
]
answer = babyagi.chat_with_functions(history)
history.extend([
    {"role": "assistant", "message": answer},
    {"role": "user", "message": "Fetch the release notes for more details."},
])
follow_up = babyagi.chat_with_functions(history)
```

Pass a function list to select tools explicitly, such as
`available_function_names=["serpapi_search_v2"]` after loading and configuring that
plugin. An explicit list is never supplemented with Parallel or replaced after
a provider fails. Pass `available_function_names=[]` for chat without tools, or
set `BABYAGI_WEB_SEARCH=off` to disable the omitted-list default. The dashboard
continues to use the functions you select with its Add/Remove controls; add
`parallel_search` or `parallel_fetch` there to enable them.

You can also call the functions directly:

```python
# One caller-owned context for this research run, including retries.
research_context = {}
results = babyagi.parallel_search(
    objective="Find the latest stable Python release",
    search_queries=["latest stable Python release"],
    search_context=research_context,
)
page = babyagi.parallel_fetch(
    urls=["https://www.python.org/downloads/"],
    objective="Stable Python release version",
    search_context=research_context,
)
```

Results retain MCP content blocks and structured data, including source URLs
and excerpts. Search objectives, queries and requested URLs are sent to Parallel
when a tool runs. Chat stores a search session identifier in metadata on the first
history message (or adds a metadata-only anchor to an empty history). Keep that
metadata when continuing or serializing the same conversation. Related search,
fetch, follow-up turns and retries retain the identifier, even after failure or
cancellation. A fresh history starts an independent chat; clear the history to
reset it. No identity is cached on the runtime or model client.

Alternatively, pass the same `search_context` dictionary to each related
`chat_with_functions`, `parallel_search` or `parallel_fetch` call. A new dictionary
starts an independent conversation or research run; an existing nonempty
`session_id` is preserved. HTTP hosts must supply and retain this context because
the chat endpoint returns only the answer, not mutated history. The dashboard
creates context with its page's chat and keeps it for every turn. Direct calls
without context omit the optional session identifier; they do not share a process
identifier. Do not change identifiers to work around service limits.

Requests have a 30-second total timeout. Service errors, including anonymous usage
limits, are surfaced without retries or provider fallback. Importing BabyAGI
only registers the tools and makes no search requests. Model credentials are
still required for chat; direct search and fetch calls do not invoke a model.

You can store `key_dependencies` directly from your code or manage them via the dashboard.

**Storing Key Dependencies from Code:**

```python
import babyagi

# Add a secret key
babyagi.add_key_wrapper('openai_api_key', 'your_openai_api_key')
```

**Adding Key Dependencies via Dashboard:**

Navigate to the dashboard and use the **add_key_wrapper** feature to securely add your secret keys.

## Execution Environment

BabyAGI automatically loads essential function packs and manages their dependencies, ensuring a seamless execution environment. Additionally, it logs all activities, including the relationships between functions, to provide comprehensive tracking of function executions and dependencies.

### Log

BabyAGI implements a comprehensive logging system to track all function executions and their interactions. The logging mechanism ensures that every function call, including its inputs, outputs, execution time, and any errors, is recorded for monitoring and debugging purposes.

**Key Logging Features:**

- **Execution Tracking:** Logs when a function starts and finishes execution, including the function name, arguments, keyword arguments, and execution time.
  
- **Error Logging:** Captures and logs any errors that occur during function execution, providing detailed error messages for troubleshooting.

- **Dependency Management:** Automatically resolves and logs dependencies between functions, ensuring that all required functions and libraries are loaded before execution.

- **Trigger Logging:** Logs the execution of triggered functions, detailing which functions were triggered by others and their respective execution outcomes.

- **Comprehensive Records:** Maintains a history of all function executions, enabling users to review past activities, understand function relationships, and analyze performance metrics.

**How Triggers Work:**

Triggers are mechanisms that allow certain functions to be automatically executed in response to specific events or actions within the system. For example, when a function is added or updated, a trigger can initiate the generation of a description for that function.

Triggers enhance the autonomy of BabyAGI by enabling automated workflows and reducing the need for manual intervention. However, it's essential to manage triggers carefully to avoid unintended recursive executions or conflicts between dependent functions.

## Dashboard

The BabyAGI dashboard offers a user-friendly interface for managing functions, monitoring executions, and handling configurations. Key features include:

- **Function Management:** Register, deregister, and update functions directly from the dashboard.

- **Dependency Visualization:** View and manage dependencies between functions to understand their relationships.

- **Secret Key Management:** Add and manage secret keys securely through the dashboard interface.

- **Logging and Monitoring:** Access comprehensive logs of function executions, including inputs, outputs, and execution times.

- **Trigger Management:** Set up triggers to automate function executions based on specific events or conditions.

**Accessing the Dashboard:**

After running your application, navigate to `http://localhost:8080/dashboard` to access the BabyAGI dashboard.
## Pre-loaded Functions Summary

BabyAGI includes two pre-loaded function packs:

1. **Default Functions (`packs/default_functions.py`):**
   - **Function Execution:** Run, add, update, or retrieve functions and versions.
   - **Key Management:** Add and retrieve secret keys.
   - **Triggers:** Add triggers to execute functions based on others.
   - **Logs:** Retrieve logs with optional filters.

2. **AI Functions (`packs/ai_generator.py`):**
   - **AI Description & Embeddings:** Auto-generate descriptions and embeddings for functions.
   - **Function Selection:** Find or choose similar functions based on prompts.

## Running a Self-Building Agent

BabyAGI includes two experimental self-building agents, showcasing how the framework can help a self-building coding agent leverage existing functions to write new ones.

### 1. `process_user_input` in the `code_writing_functions` pack

This function first determines whether to use an existing function or generate new ones. If new functions are needed, it breaks them down into smaller reusable components and combines them into a final function.

Try this:

~~~python
import babyagi

babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])
babyagi.load_functions("drafts/code_writing_functions")

babyagi.process_user_input("Grab today's score from ESPN and email it to test@test.com")
~~~

When you run this, you will see the functions being generated in the shell and new functions will be available in the dashboard once completed.

### 2. `self_build` in the `self_build` pack

This function takes a user description and generates X distinct tasks that a user might ask an AI assistant. Each task is processed by `process_user_input`, creating new functions if no existing ones suffice.

Try this:

~~~python
import babyagi

babyagi.add_key_wrapper('openai_api_key', os.environ['OPENAI_API_KEY'])
babyagi.load_functions("drafts/code_writing_functions")
babyagi.load_functions("drafts/self_build")

babyagi.self_build("A sales person at an enterprise SaaS company.", 3)
~~~

This will generate 3 distinct tasks a salesperson might ask an AI assistant and create functions to handle those.

*The functions will be generated and stored in the dashboard, but note that the generated code is minimal and may need improvement.

![alt text](https://github.com/yoheinakajima/babyagi_staging/blob/main/self_build.png?raw=true)



**Warning:** These draft features are experimental concepts and may not function as intended. They require significant improvements and should be used with caution.


## Contributing

Contributions are greatly appreciatedly, but candidly I have not been great at managing PRs. Please be patient as things will move slow while I am working on this alone (on nights and weekends). I may start by building a small core crew before collaborating with a larger group.

If you are a dev, investor, friend of open-source and interesting supporting AI work I do, please fill [this form](https://forms.gle/UZLyT75HQULr8XNUA) (I have a few fun initiatives coming up!)

## License

BabyAGI is released under the MIT License. See the [LICENSE](LICENSE) file for more details.
