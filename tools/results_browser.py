#!/usr/bin/env python3
import os
import sys

project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(project_root)

import curses
import argparse
import openai
import pinecone
from dotenv import load_dotenv
import textwrap
from components.context_storage.IContextStorage import ContextStorage

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

# Context Storage config
TASK_STORAGE_NAME = os.getenv("TASK_STORAGE_NAME", os.getenv("TABLE_NAME", "tasks"))
CONTEXT_STORAGE_TYPE = os.getenv("CONTEXT_STORAGE_TYPE", "pinecone").lower()
context_storage_options = {}

# Pinecone config
if CONTEXT_STORAGE_TYPE == "pinecone":
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
    PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "")

    assert PINECONE_API_KEY, "PINECONE_API_KEY is missing from .env"
    assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT is missing from .env"

    def get_ada_embedding(text):
        text = text.replace("\n", " ")
        return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

    from components.context_storage.IContextStorage import PineconeOptions
    context_storage_options = PineconeOptions(PINECONE_API_KEY, PINECONE_ENVIRONMENT, get_ada_embedding, TASK_STORAGE_NAME)

# Weaviate config
elif CONTEXT_STORAGE_TYPE == "weaviate":
    WEAVIATE_HOST = os.getenv("WEAVIATE_HOST", "")
    WEAVIATE_VECTORIZER = os.getenv("WEAVIATE_VECTORIZER", "")

    assert WEAVIATE_HOST, "WEAVIATE_HOST is missing from .env"
    assert WEAVIATE_VECTORIZER, "WEAVIATE_VECTORIZER is missing from .env"

    from components.context_storage.IContextStorage import WeaviateOptions
    context_storage_options = WeaviateOptions(WEAVIATE_HOST, WEAVIATE_VECTORIZER, TASK_STORAGE_NAME)

else:
    raise Exception("CONTEXT_STORAGE_TYPE must be a valid option (pinecone | weaviate)")

# Function to query records from the Pinecone index
def query_records(index: ContextStorage, query, top_k=1000):
    results = index.query(query, n=top_k)
    return [{"name": f"{task.data['task']}", "result": f"{task.data['result']}"} for task in results]

def draw_tasks(stdscr, tasks, scroll_pos, selected):
    y = 0
    h, w = stdscr.getmaxyx()
    for idx, task in enumerate(tasks[scroll_pos:], start=scroll_pos):
        if y >= h:
            break
        task_name = f'{task["name"]}'
        truncated_str = task_name[:w-1]
        if idx == selected:
            stdscr.addstr(y, 0, truncated_str, curses.A_REVERSE)
        else:
            stdscr.addstr(y, 0, truncated_str)
        y += 1

def draw_result(stdscr, task):
    task_name = f'Task: {task["name"]}'
    task_result = f'Result: {task["result"]}'

    _, w = stdscr.getmaxyx()
    task_name_wrapped = textwrap.wrap(task_name, width=w)

    for i, line in enumerate(task_name_wrapped):
        stdscr.addstr(i, 0, line)
    
    y, _ = stdscr.getyx()
    stdscr.addstr(y+1, 0, '------------------')
    stdscr.addstr(y+2, 0, task_result)

def draw_summary(stdscr, objective, tasks, start, num):
    stdscr.box()
    summary_text = f'{len(tasks)} tasks ({start}-{num}) | {objective}'
    stdscr.addstr(1, 1, summary_text[:stdscr.getmaxyx()[1] - 2])

def main(stdscr):
    # Initialize Pinecone
    index = ContextStorage.factory(CONTEXT_STORAGE_TYPE, context_storage_options)

    curses.curs_set(0)
    stdscr.timeout(1000)

    h, w = stdscr.getmaxyx()
    left_w = w // 2
    visible_lines = h - 3

    scroll_pos = 0
    selected = 0

    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Query Pinecone index using a string.")
    parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
    main objective description. Doesn\'t need to be quoted.
    if not specified, get objective from environment.
    ''', default=[os.getenv("OBJECTIVE", "")])
    args = parser.parse_args()

    # Query records from the index
    objective = ' '.join(args.objective).strip().replace("\n", " ")
    retrieved_tasks = query_records(index, objective)

    while True:
        stdscr.clear()
        draw_tasks(stdscr.subwin(h-3, left_w, 0, 0), retrieved_tasks, scroll_pos, selected)
        draw_result(stdscr.subwin(h, w - left_w, 0, left_w), retrieved_tasks[selected])
        draw_summary(stdscr.subwin(3, left_w, h - 3, 0), objective, retrieved_tasks, scroll_pos+1, scroll_pos+h-3)

        stdscr.refresh()
        key = stdscr.getch()

        if key == ord('q') or key == 27:
            break
        elif key == curses.KEY_UP and selected > 0:
            selected -= 1
            if selected < scroll_pos:
                scroll_pos -= 1
        elif key == curses.KEY_DOWN and selected < len(retrieved_tasks) - 1:
            selected += 1
            if selected - scroll_pos >= visible_lines:
                scroll_pos += 1

curses.wrapper(main)