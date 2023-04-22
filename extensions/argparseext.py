import os
import sys
import importlib
import argparse

def can_import(module_name):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False

# Extract the env filenames in the -e flag only
# Ignore any other arguments
def parse_dotenv_extensions(argv):
    env_argv = []
    if '-e' in argv:
        tmp_argv = argv[argv.index('-e') + 1:]
        parsed_args = []
        for arg in tmp_argv:
            if arg.startswith('-'):
                break
            parsed_args.append(arg)
        env_argv = ['-e'] + parsed_args

    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', nargs='+', help='''
    filenames for additional env variables to load
    ''', default=os.getenv("DOTENV_EXTENSIONS", "").split(' '))

    return parser.parse_args(env_argv).env

def parse_arguments():
    dotenv_extensions = parse_dotenv_extensions(sys.argv)
    # Check if we need to load any additional env files
    # This allows us to override the default .env file
    # and update the default values for any command line arguments
    if dotenv_extensions:
        from extensions.dotenvext import load_dotenv_extensions
        load_dotenv_extensions(parse_dotenv_extensions(sys.argv))

    # Now parse the full command line arguments
    parser = argparse.ArgumentParser(
        add_help=False,
    )
    parser.add_argument('objective', nargs='*', metavar='<objective>', help='''
    main objective description. Doesn\'t need to be quoted.
    if not specified, get objective from environment.
    ''', default=[os.getenv("OBJECTIVE", "")])
    parser.add_argument('-n', '--name', required=False, help='''
    instance name.
    if not specified, get the instance name from environment.
    ''', default=os.getenv("INSTANCE_NAME", os.getenv("BABY_NAME", "BabyAGI")))
    parser.add_argument('-m', '--mode', choices=['n', 'none', 'l', 'local', 'd', 'distributed'], help='''
    cooperative mode type
    ''', default='none')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-t', '--task', metavar='<initial task>', help='''
    initial task description. must be quoted.
    if not specified, get initial_task from environment.
    ''', default=os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", "")))
    group.add_argument('-j', '--join', action='store_true', help='''
    join an existing objective.
    install cooperative requirements.
    ''')
    group2 = parser.add_mutually_exclusive_group()
    group2.add_argument('-4', '--gpt-4', dest='llm_model', action='store_const', const="gpt-4", help='''
    use GPT-4 instead of the default model.
    ''')
    group2.add_argument('-l', '--llama', dest='llm_model', action='store_const', const="llama", help='''
    use LLaMa instead of the default model. Requires llama.cpp.
    ''')
    # This will parse -e again, which we want, because we need
    # to load those in the main file later as well
    parser.add_argument('-e', '--env', nargs='+', help='''
    filenames for additional env variables to load
    ''', default=os.getenv("DOTENV_EXTENSIONS", "").split(' '))
    parser.add_argument('-h', '-?', '--help', action='help', help='''
    show this help message and exit
    ''')

    args = parser.parse_args()

    llm_model = args.llm_model if args.llm_model else os.getenv("LLM_MODEL", os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo")).lower()

    dotenv_extensions = args.env

    instance_name = args.name
    if not instance_name:
        print("\033[91m\033[1m" + "BabyAGI instance name missing\n" + "\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    module_name = "ray"
    cooperative_mode = args.mode
    if cooperative_mode in ['l', 'local'] and not can_import(module_name):
        print("\033[91m\033[1m"+f"Local cooperative mode requires package {module_name}\nInstall:  pip install -r extensions/requirements.txt\n" + "\033[0m\033[0m")
        parser.print_help()
        parser.exit()
    elif cooperative_mode in ['d', 'distributed']:
        print("\033[91m\033[1m" + "Distributed cooperative mode is not implemented yet\n" + "\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    join_existing_objective = args.join
    if join_existing_objective and cooperative_mode in ['n', 'none']:
        print("\033[91m\033[1m"+f"Joining existing objective requires local or distributed cooperative mode\n" + "\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    objective = ' '.join(args.objective).strip()
    if not objective:
        print("\033[91m\033[1m" + "No objective specified or found in environment.\n" + "\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    initial_task = args.task
    if not initial_task and not join_existing_objective:
        print("\033[91m\033[1m" + "No initial task specified or found in environment.\n" + "\033[0m\033[0m")
        parser.print_help()
        parser.exit()

    return objective, initial_task, llm_model, dotenv_extensions, instance_name, cooperative_mode, join_existing_objective