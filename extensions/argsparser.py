import os
import argparse
import importlib

def parse_arguments():
    parser = argparse.ArgumentParser(
        add_help=False,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog="""
cooperative mode enables multiple instances of babyagi to work towards the same objective.
 * none        - (default) no cooperation, each instance works on its own list of tasks
 * local       - local machine cooperation
                 uses ray to share the list of tasks for an objective
 * distributed - distributed cooperation (not implemented yet)
                 uses pinecone to share the list of tasks for an objective

examples:
 * start solving world hunger by creating initial list of tasks using GPT-4:
     %(prog)s -m local -t "Create initial list of tasks" -4 Solve world hunger
 * join the work on solving world hunger using GPT-3:
     %(prog)s -m local -j Solve world hunger
"""
    )
    parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
    main objective description. Doesn\'t need to be quoted.
    if not specified, get objective from environment.
    ''', default=[os.getenv("OBJECTIVE", "")])
    parser.add_argument('-n', '--name', required=False, help='''
    babyagi instance name.
    if not specified, get baby_name from environment.
    ''', default=os.getenv("BABY_NAME", "BabyAGI"))
    parser.add_argument('-m', '--mode', choices=['n', 'none', 'l', 'local', 'd', 'distributed'], help='''
    cooperative mode type
    ''', default='none')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t', '--task', metavar='<initial task>', help='''
    initial task description. must be quoted.
    if not specified, get INITIAL_TASK from environment.
    ''', default=os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", "")))
    group.add_argument('-j', '--join', action='store_true', help='''
    join an existing objective.
    install cooperative requirements.
    ''')
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-4', '--gpt-4', dest='use_gpt4', action='store_true', help='''
    use GPT-4 instead of GPT-3
    ''')
    group2.add_argument('-l', '--llama', dest='use_llama', action='store_true', help='''
    use LLaMa instead of GPT-3
    ''')
    parser.add_argument('-h', '-?', '--help', action='help', help='''
    show this help message and exit
    ''')

    args = parser.parse_args()

    baby_name = args.name
    if not baby_name:
        print("\033[91m\033[1m"+"BabyAGI instance name missing\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    use_gpt4 = args.use_gpt4
    use_llama = args.use_llama

    def can_import(module_name):
        try:
            importlib.import_module(module_name)
            return True
        except ImportError:
            return False

    module_name = "ray"
    cooperative_mode = args.mode
    if cooperative_mode in ['l', 'local'] and not can_import(module_name):
        print("\033[91m\033[1m"+f"Local cooperative mode requires package {module_name}\nInstall:  pip install -r requirements-cooperative.txt\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()
    elif cooperative_mode in ['d', 'distributed']:
        print("\033[91m\033[1m"+"Distributed cooperative mode is not implemented yet\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    join_existing_objective = args.join
    if join_existing_objective and cooperative_mode in ['n', 'none']:
        print("\033[91m\033[1m"+f"Joining existing objective requires local or distributed cooperative mode\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    objective = ' '.join(args.objective).strip()
    if not objective:
        print("\033[91m\033[1m"+"No objective specified or found in environment.\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    initial_task = args.task
    if not initial_task and not join_existing_objective:
        print("\033[91m\033[1m"+"No initial task specified or found in environment.\n"+"\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    return objective, initial_task, use_gpt4, use_llama, baby_name, cooperative_mode, join_existing_objective