from dotenv import load_dotenv

def load_dotenv_extensions(dotenv_files):
    for dotenv_file in dotenv_files:
        load_dotenv(dotenv_file)
