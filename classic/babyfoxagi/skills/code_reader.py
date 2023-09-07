from skills.skill import Skill
import openai
import os

class CodeReader(Skill):
    name = 'code_reader'
    description = "A skill that finds a file's location in it's own program's directory and returns its contents."
    api_keys_required = ['openai']

    def __init__(self, api_keys, main_loop_function):
        super().__init__(api_keys, main_loop_function)

    def execute(self, params, dependent_task_outputs, objective):
        if not self.valid:
            return

        dir_structure = self.get_directory_structure(self.get_top_parent_path(os.path.realpath(__file__)))
        print(f"Directory structure: {dir_structure}")
        example_dir_structure = {'.': {'main.py': None}, 'skills': {'__init__.py': None, 'web_scrape.py': None, 'skill.py': None, 'test_skill.py': None, 'text_completion.py': None, 'web_search.py': None, 'skill_registry.py': None, 'directory_structure.py': None, 'code_reader.py': None}, 'tasks': {'task_registry.py': None}, 'output': {}}
        example_params = "Analyze main.py"
        example_response = "main.py"
      
        task_prompt = f"Find a specific file in a directory and return only the file path, based on the task description below. Always return a directory.###The directory structure is as follows: \n{example_dir_structure}\nYour task: {example_params}\n###\nRESPONSE:{example_response} ###The directory structure is as follows: \n{dir_structure}\nYour task: {params}\n###\nRESPONSE:"
      
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": task_prompt}
        ]
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.2,
            max_tokens=1500,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0
        )
        file_path = response.choices[0].message['content'].strip()
        print(f"AI suggested file path: {file_path}")

        try:
            with open(file_path, 'r') as file:
                file_content = file.read()
                #print(f"File content:\n{file_content}")
                return file_content
        except FileNotFoundError:
            print("File not found. Please check the AI's suggested file path.")
            return None

    def get_directory_structure(self, start_path):
        dir_structure = {}
        ignore_dirs = ['.','__init__.py', '__pycache__', 'pydevd', 'poetry','venv']  # add any other directories to ignore here
    
        for root, dirs, files in os.walk(start_path):
            dirs[:] = [d for d in dirs if not any(d.startswith(i) for i in ignore_dirs)]  # exclude specified directories
            files = [f for f in files if not f[0] == '.' and f.endswith('.py')]  # exclude hidden files and non-Python files

            current_dict = dir_structure
            path_parts = os.path.relpath(root, start_path).split(os.sep)
            for part in path_parts:
                if part:  # skip empty parts
                    if part not in current_dict:
                        current_dict[part] = {}
                    current_dict = current_dict[part]
            for f in files:
                current_dict[f] = None

        return dir_structure
    
    def get_top_parent_path(self, current_path):
        relative_path = ""
        while True:
            new_path = os.path.dirname(current_path)
            if new_path == '/home/runner/BabyfoxAGIUI/skills':  # reached the top
                return '/home/runner/BabyfoxAGIUI'
            current_path = new_path
            relative_path = os.path.join("..", relative_path)

        return relative_path
