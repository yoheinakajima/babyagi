import os
import argparse

def parse_arguments():
    parser = argparse.ArgumentParser(
        add_help=False,
    )
    parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
    main objective description. Doesn\'t need to be quoted.
    if not specified, get objective from environment.
    ''', default=[os.getenv("objective", "")])
    parser.add_argument('-t', '--task', metavar='<initial task>', help='''
    initial task description. must be quoted.
    if not specified, get initial_task from environment.
    ''', default=os.getenv("initial_task", os.getenv("FIRST_TASK", "")))
    parser.add_argument('-4', '--gpt-4', dest='use_gpt4', action='store_true', help='''
    use GPT-4 instead of GPT-3
    ''')
    parser.add_argument('-h', '-?', '--help', action='help', help='''
    show this help message and exit
    ''')

    args = parser.parse_args()

    use_gpt4 = args.use_gpt4

    objective = ' '.join(args.objective).strip()
    if not objective:
        print("\033[91m\033[1m"+"No objective specified or found in environment.\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    initial_task = args.task
    if not initial_task:
        print("\033[91m\033[1m"+"No initial task specified or found in environment.\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    return objective, initial_task, use_gpt4