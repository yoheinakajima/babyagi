import tkinter as tk
import threading
import webbrowser
from babyagi import add_task, run_babyagi
from tkinter import simpledialog

def add_task_from_gui():
    task_name = task_entry.get()
    add_task({"task_name": task_name})
    task_entry.delete(0, tk.END)

babyagi_thread = None
running = False

def toggle_babyagi():
    global babyagi_thread
    global running

    if running:
        running = False
        start_stop_button.config(text="Start")
    else:
        running = True
        babyagi_thread = threading.Thread(target=run_babyagi)
        babyagi_thread.start()
        start_stop_button.config(text="Stop")

trello_board_url = None
first_click = True

def open_trello_board():
    global trello_board_url
    global first_click

    if first_click:
        trello_board_url = simpledialog.askstring("Trello Board URL", "Enter the Trello board URL:")
        first_click = False

    if trello_board_url:
        webbrowser.open(trello_board_url)

root = tk.Tk()
root.title("TaskEvo GUI")

task_label = tk.Label(root, text="Task Name:")
task_entry = tk.Entry(root, width=50)
add_button = tk.Button(root, text="Add Task", command=add_task_from_gui)
start_stop_button = tk.Button(root, text="Start", command=toggle_babyagi)
trello_link = tk.Button(root, text="Open Trello Board", command=open_trello_board)

task_label.grid(row=0, column=0, padx=10, pady=10)
task_entry.grid(row=0, column=1, padx=10, pady=10)
add_button.grid(row=1, column=1, padx=10, pady=10)
start
