from skills.skill import Skill
import os

class DirectoryStructure(Skill):
    name = 'directory_structure'
    description = "A tool that outputs the file and folder structure of its top parent folder."

    def __init__(self, api_keys=None):
        super().__init__(api_keys)

    def execute(self, params, dependent_task_outputs, objective):
        # Get the current script path
        current_script_path = os.path.realpath(__file__)

        # Get the top parent directory of current script
        top_parent_path = self.get_top_parent_path(current_script_path)
        # Get the directory structure from the top parent directory
        dir_structure = self.get_directory_structure(top_parent_path)

        return dir_structure

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
        #print("#############################")
        #print(str(current_dict)[0:100])
        return dir_structure
    
    

    def get_top_parent_path(self, current_path):
        relative_path = ""
        while True:
            new_path = os.path.dirname(current_path)
            print(new_path)
            if new_path == '/home/runner/BabyElfAGI/skills':  # reached the top
            #if new_path == current_path:  # reached the top
                #return relative_path
                return '/home/runner/BabyElfAGI'
            current_path = new_path
            relative_path = os.path.join("..", relative_path)
            print(relative_path)