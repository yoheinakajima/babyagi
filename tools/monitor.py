import os
import time
import ray
import shutil

ray.init()

class Actor:
    def __init__(self):
        self.message = 'Hello, World!'

    def get_message(self):
        return self.message

actor = Actor()
actor_ref = ray.put(actor)

def print_centered(message):
    columns, _ = shutil.get_terminal_size()
    padding = ' ' * ((columns - len(message)) // 2)
    print(padding + message)

while True:
    os.system('clear')
    actor_instance = ray.get(actor_ref)
    print_centered(actor_instance.get_message())
    time.sleep(30)