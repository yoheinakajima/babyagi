import os
import time
import ray

ray.init()

class Actor:
    def __init__(self):
        self.message = 'Hello, World!'

    def get_message(self):
        return self.message

actor = Actor()
actor_ref = ray.put(actor)

while True:
    os.system('clear')
    actor_instance = ray.get(actor_ref)
    print(actor_instance.get_message())
    time.sleep(30)