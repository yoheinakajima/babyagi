#!/usr/bin/env python3
import os
import time
from collections import deque
from dotenv import load_dotenv
from agents.IAgent import AgentData
from agents.browser_agent import BrowserAgent
from agents.logger_agent import LoggerAgent
from agents.task_prioritiser_agent import ObjectiveCompletionAgent
from completion.openai_provider import OpenAiProvider
from task.task_processor import TaskProcessor
from vector.weaviate import Weaviate

# Load default environment variables (.env)
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

#options = Weaviate.WeaviateOptions(host='http://localhost:8080')
#vector_client = Weaviate(options)
browser_agent = BrowserAgent()
openai_provider = OpenAiProvider(OPENAI_API_KEY)
logger = LoggerAgent()
task_processor = TaskProcessor()
list_of_tasks = deque([])
completed_tasks = deque([])

agent_data = AgentData(objective='Plan my week end glamping around cambridge UK next May.',
                       active_tasks=list_of_tasks,
                       completed_tasks=completed_tasks,
                       vectordb=None,
                       open_ai=openai_provider,
                       browser=browser_agent,
                       logger=logger)

logger.log(f"Starting solving: {agent_data.objective}")

task_processor.task_creation_agent.create_first_task(agent_data)
max_days = 6

for day in range(1, max_days):
    if not list_of_tasks:
        logger.log("No more tasks to process")
        break
    
    logger.log(f"Day {day}: Starting Task {list_of_tasks[0]}")
    warning = f"""You have a maximum of {max_days} tasks to complete the objective. This is task {day}."""
    task_processor.process_task(agent_data, warning)
    
    time.sleep(1)

ObjectiveCompletionAgent().conclude(agent_data)
logger.close()