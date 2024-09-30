@func.register_function(
    metadata={"description": "Returns the current directory and recursively lists all files and folders, excluding hidden files, folders (those starting with a '.'), and the '__pycache__' folder. The output omits the current directory prefix from file paths for readability."},
    imports=["os"]
)
def get_full_directory_contents_cleaned():
    current_directory = os.getcwd()  # Get current working directory
    directory_structure = {}

    # Walk through the directory and its subdirectories
    for root, dirs, files in os.walk(current_directory):
        # Filter out hidden directories, '__pycache__', and hidden files
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != '__pycache__']
        files = [f for f in files if not f.startswith('.')]

        # Remove the current directory path from the root
        relative_root = root.replace(current_directory, "").lstrip(os.sep)
        directory_structure[relative_root] = {
            "folders": dirs,
            "files": files
        }

    return {"current_directory": current_directory, "directory_structure": directory_structure}
