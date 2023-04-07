from plugins.vectors.IVectorDB import VectorDB, get_vector_client
from plugins.agents.task_creation import TaskCreationAgent
from plugins.agents.task_prioritization import TaskPrioritizationAgent
from plugins.agents.task_execution import TaskExecutionAgent
from plugins.agents.IAgent import Task, Agent, AgentData
from plugins.reporting.reporter import Reporter
from plugins.completions.ICompletionClient import get_completion_client

from collections import deque
import time
import sys
import os

# Load .env
from dotenv import load_dotenv
load_dotenv()

# Set Objective
OBJECTIVE = sys.argv[1] if len(sys.argv) > 1 else os.getenv("OBJECTIVE", "")
assert OBJECTIVE, "OBJECTIVE environment variable is missing from .env"

# Initialize Task List
YOUR_FIRST_TASK = os.getenv("FIRST_TASK", "")
assert YOUR_FIRST_TASK, "FIRST_TASK environment variable is missing from .env"
task_list = deque([Task(1, YOUR_FIRST_TASK)])

# Initialize Completion Client
COMPLETION_API_KEY = os.getenv("COMPLETION_API_KEY", "")
assert COMPLETION_API_KEY, "COMPLETION_API_KEY environment variable is missing from .env"
COMPLETION_MODEL = os.getenv("COMPLETION_MODEL", "")
assert COMPLETION_MODEL, "COMPLETION_MODEL environment variable is missing from .env"
completion_client = get_completion_client(COMPLETION_API_KEY, COMPLETION_MODEL)

# Initialize VectorDB
VECTOR_TYPE = os.getenv("VECTOR_TYPE", "")
assert VECTOR_TYPE, "VECTOR_TYPE environment variable is missing from .env"

YOUR_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert YOUR_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

VECTOR_HOST = os.getenv("VECTOR_HOST", None)

vector: VectorDB = get_vector_client(VECTOR_TYPE, VECTOR_HOST, YOUR_TABLE_NAME)
assert vector, "Failed to initialize the vector db"

agents: dict[str, list[Agent]] = {
    "create": [TaskCreationAgent()],
    "prioritize": [TaskPrioritizationAgent()],
    "execute": [TaskExecutionAgent()],
}

data = AgentData(
    objective=OBJECTIVE,
    active_tasks=task_list,
    completed_tasks=[],
    completion_client=completion_client,
    vectordb=vector,
)

while True:
    if data.active_tasks:
        # Print the task list
        Reporter.output_task_list(data.active_tasks)

        # Step 1: Pull the first task
        next_task = data.active_tasks[0]
        Reporter.output_next_task(next_task)

        # Send to execution function to complete the task based on the context
        for agent in agents['execute']:
            data: AgentData = agent.exec(data)
        next_task = data.completed_tasks[-1]
        Reporter.output_task_result(next_task)

        # Store Task in VectorDB
        vector.insert_data(next_task)
    
    # Step 3: Create new tasks
    for agent in agents['create']:
        data: AgentData = agent.exec(data)

    # Step 4: Reprioritize tasks
    for agent in agents['prioritize']:
        data: AgentData = agent.exec(data)
    
    time.sleep(1)