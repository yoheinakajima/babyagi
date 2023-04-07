#!/usr/bin/env python3
import os
import curses
import argparse
import openai
import pinecone
from dotenv import load_dotenv
import textwrap

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
assert OPENAI_API_KEY, "OPENAI_API_KEY environment variable is missing from .env"

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "")
assert PINECONE_API_KEY, "PINECONE_API_KEY environment variable is missing from .env"

PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENVIRONMENT", "us-east1-gcp")
assert PINECONE_ENVIRONMENT, "PINECONE_ENVIRONMENT environment variable is missing from .env"

# Table config
PINECONE_TABLE_NAME = os.getenv("TABLE_NAME", "")
assert PINECONE_TABLE_NAME, "TABLE_NAME environment variable is missing from .env"

# Function to query records from the Pinecone index
def query_records(index, query, top_k=1000):
    results = index.query(query, top_k=top_k, include_metadata=True)
    return [{"name": f"{task.metadata['task']}", "result": f"{task.metadata['result']}"} for task in results.matches]

# Get embedding for the text
def get_ada_embedding(text):
    return openai.Embedding.create(input=[text], model="text-embedding-ada-002")["data"][0]["embedding"]

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
    pinecone.init(api_key=PINECONE_API_KEY)

    # Connect to the objective index
    index = pinecone.Index(PINECONE_TABLE_NAME)

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
    retrieved_tasks = query_records(index, get_ada_embedding(objective))

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