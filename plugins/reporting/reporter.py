from collections import deque
from ..agents.IAgent import Task

def print_color(color: str, text: str):
    COLORS = {
        "red": "\033[31m",
        "green": "\033[32m",
        "yellow": "\033[33m",
        "blue": "\033[34m",
        "magenta": "\033[35m",
        "cyan": "\033[36m",
        "reset": "\033[0m"
    }
    if color.lower() not in COLORS:
        raise ValueError(f"Invalid color specified: {color}")
    print(f"{COLORS[color.lower()]}{text}{COLORS['reset']}")

class Reporter:
    def output_task_list(task_list: deque[Task]): 
        print_color("magenta", "\n*****TASK LIST*****")
        for task in task_list:
            print(f"{task.id}: {task.description}")

    def output_next_task(task: Task):
        print_color("green", "\n*****NEXT TASK*****")
        print(f"{task.id}: {task.description}")

    def output_task_result(task: Task):
        print_color("yellow", "\n*****TASK RESULT*****")
        print(task.result)
