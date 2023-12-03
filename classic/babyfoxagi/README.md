### Author's Note

BabyFoxAGI is the 5th mod of BabyAGI. The earlier 4 were [BabyBeeAGI](https://twitter.com/yoheinakajima/status/1652732735344246784?lang=en), [BabyCatAGI](https://twitter.com/yoheinakajima/status/1657448504112091136), [BabyDeerAGI](https://twitter.com/yoheinakajima/status/1666313838868992001), and [BabyElfAGI](https://twitter.com/yoheinakajima/status/1678443482866933760). Following the evolution will be the easiest way to understand BabyFoxAGI. Please check out [the tweet thread introducing BabyFoxAGI](https://twitter.com/yoheinakajima/status/1697539193768116449) for a quick overview.

### New Features in BabyFoxAGI

In BabyFoxAGI, the two newest features are:

1. **Self-Improvement (Also known as [FOXY Method](https://twitter.com/yoheinakajima/status/1685894298536148992))**: This helps it improve its task list building.
2. **[BabyAGI Experimental UI](https://twitter.com/yoheinakajima/status/1693153307454546331)**: In this feature, the chat is separated from task/output.

Notable in the chat is the ability to either run one skill quickly or generate a task list and chain skills, where the you see BabyAGI (moved to babyagi.py) comes in. main.py is now the back-end to the Python Flask based chat app (public/templates folder).

### Known Issues and Limitations

I had issues with parallel tasks within BabyAGI, so removed that for now. I'm also not streaming the task list or in-between work from these task list runs to the UI. For now, you'll have to monitor that in the console. And in general, lots more room for improvement... but wanted to get this out there :)

## Getting Started

These instructions will guide you through the process of setting up Classic BabyFoxAGI on your local machine.

### Prerequisites

Make sure you have the following software installed:

- Git ([Download & Install Git](https://git-scm.com/downloads))
- Python 3.8-3.11 ([Download & Install Python](https://www.python.org/downloads/))
- Pip (usually installed with Python)

### Clone the Repository

To clone this specific folder (`classic/babyfoxagi`) from the GitHub repository, open a terminal and run the following commands:

```bash
# Navigate to the directory where you want to clone the project
cd your/desired/directory

# Clone the entire repository
git clone https://github.com/yoheinakajima/babyagi.git

# Move into the cloned repository
cd babyagi

# Navigate to the 'classic/babyfoxagi' folder
cd classic/babyfoxagi
```

### Install Dependencies

Install **requirements.txt**, to get the required packages:

```bash
# Install required packages
pip install -r requirements.txt
```

Note: If you are using a Python environment manager like conda, make sure to activate your environment before running the pip commands.

### Configuration

Create a .env file in the classic/babyfoxagi directory to store your API keys.

```bash
# Create a .env file
touch .env

# Open the .env file with a text editor and add your API keys
echo "OPENAI_API_KEY=your_openai_api_key_here" >> .env
# Add other API keys as needed for other tools (e.g., Airtable)
echo "SERPAPI_API_KEY=your_serpapi_api_key_here" >> .env
echo "AIRTABLE_API_KEY=your_airtable_api_key_here" >> .env
```

For other tools like airtable_search, you may also need to specify additional configurations like BASE, TABLE, and COLUMN in the airtable_search.py file.

### Running the Project

After cloning the repository, installing the dependencies, and setting up the .env file, just run:

```bash
python main.py
```

# BabyFoxAGI - Overview

BabyFoxAGI is an experimental chat-based UI that can use a variety of skills to accomplish tasks, displayed in a separate panel from the Chat UI, allowing for parallel execution of tasks. Tasks can be accomplished quickly using one skill, or by generating a tasklist and chaining multiple tasks/skills together.

## Skills

Skills that are included include text_completion, web_search, drawing (uses html canvas), documentation_search, code_reader, skill_saver, airtable_search, and call_babyagi. Please read through each skill to understand them better.

## Components

The project consists mainly of two Python scripts (`main.py` and `babyagi.py`) and a client-side JavaScript file (`Chat.js`), along with an HTML layout (`index.html`).

### main.py

#### Role

Acts as the entry point for the Flask web application and handles routes, API calls, and ongoing tasks.

#### Key Features

- Flask routes for handling HTTP requests.
- Integration with OpenAI's API for text summarization and skill execution.
- Management of ongoing tasks and their statuses.

### Chat.js

#### Role

Handles the client-side interaction within the web interface, including capturing user input and displaying messages and task statuses.

#### Key Features

- Dynamic chat interface for user interaction.
- HTTP requests to the Flask backend for task initiation and status checks.
- Presentation layer for task status and results.

### index.html

#### Role

Provides the layout for the web interface, including a chat box for user interaction and an objectives box for task display.

#### Key Features

- HTML layout that accommodates the chat box and objectives box side-by-side.

### babyagi.py

#### Role

Acts as the central orchestrator for task execution, coordinating with various skills to accomplish a predefined objective.

#### Key Features

- Task and skill registries to manage the execution.
- Main execution loop that iteratively performs tasks based on dependencies and objectives.
- Optional feature to reflect on task outputs and potentially generate new tasks.

## Flow of Execution

1. The user interacts with the chat interface, sending commands or inquiries.
2. `main.py` receives these requests and uses OpenAI's API to determine the next steps, which could include executing a skill or creating a task list.
3. If tasks are to be executed, `main.py` delegates to `babyagi.py`.
4. `babyagi.py` uses its main execution loop to perform tasks in the required sequence, based on dependencies and the main objective.
5. The output or status of each task is sent back to the client-side via Flask routes, and displayed using `Chat.js`.

## Notes

- The system leverages `.env` for API key management.
- `.ndjson` files are used for persistent storage of chat and task statuses.
- There is an optional `REFLECTION` feature in `babyagi.py` that allows the system to reflect on task outputs and potentially generate new tasks.

This overview provides a comprehensive look into the functionalities and execution flow of the project, offering both high-level insights and low-level details.
