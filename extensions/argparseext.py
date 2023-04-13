import os
import sys
import argparse

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
    parser.add_argument('-t', '--task', metavar='<initial task>', help='''
    initial task description. must be quoted.
    if not specified, get initial_task from environment.
    ''', default=os.getenv("INITIAL_TASK", os.getenv("FIRST_TASK", "")))
    group = parser.add_mutually_exclusive_group()
    group.add_argument('-4', '--gpt-4', dest='openai_api_model', action='store_const', const="gpt-4", help='''
    use GPT-4 instead of the default model.
    ''', default=os.getenv("OPENAI_API_MODEL", "gpt-3.5-turbo"))
    group.add_argument('-l', '--llama', dest='openai_api_model', action='store_const', const="llama", help='''
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

    openai_api_model = args.openai_api_model

    dotenv_extensions = args.env

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

    return objective, initial_task, openai_api_model, dotenv_extensions