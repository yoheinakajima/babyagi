import os
import time
import ray
import curses

ray.init()

class Actor:
    def __init__(self):
        self.message = 'Hello, World!'

    def get_message(self):
        return self.message

actor = Actor()
actor_ref = ray.put(actor)

def print_centered(stdscr, message):
    stdscr.clear()
    height, width = stdscr.getmaxyx()
    y = height // 2
    x = (width - len(message)) // 2
    stdscr.addstr(y, x, message)
    stdscr.refresh()


def main(stdscr):
    while True:
        actor_instance = ray.get(actor_ref)
        print_centered(stdscr, actor_instance.get_message())
        time.sleep(30)


if __name__ == '__main__':
    curses.wrapper(main)