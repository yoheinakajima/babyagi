# packs/default_functions.py

from babyagi.functionz.core.framework import func
from datetime import datetime
from typing import Optional, Dict, Any, List

@func.register_function()
def execute_function_wrapper(function_name: str, *args, **kwargs):
    # Create an initial log for the wrapper
    wrapper_log_id = func.db.add_log(
        function_name="execute_function_wrapper",
        message="Wrapper execution started.",
        timestamp=datetime.now(),
        params={"function_name": function_name, "args": args, "kwargs": kwargs},
        output=None,
        time_spent=0,
        parent_log_id=None,
        triggered_by_log_id=None,
        log_type='started'
    )
    # Execute the function with the wrapper's log ID as the parent ID
    result = func.execute_function(function_name, *args, parent_log_id=wrapper_log_id, **kwargs)

    # Update the wrapper log after execution
    func.db.update_log(wrapper_log_id, output=result, log_type='success', message="Wrapper execution completed.")
    return result


@func.register_function(
    metadata={
        "description": "Dynamically adds a new function to the system with the provided code and metadata."
    },
    imports=["typing"]
)
def add_new_function(
    name: str,
    code: str,
    metadata: dict = None,
    imports: list = None,
    dependencies: list = None,
    key_dependencies: list = None,
    triggers: list = None
) -> bool:

    try:
        func.registrar.add_function(
            name=name,
            code=code,
            metadata=metadata,
            imports=imports,
            dependencies=dependencies,
            key_dependencies=key_dependencies,
            triggers=triggers
        )
        #print(f"Function '{name}' added successfully.")
        return True
    except Exception as e:
        print(f"Error adding function '{name}': {str(e)}")
        return False


@func.register_function()
def function_added_or_updated(action=None, triggered_function_name=None):
    """
    Triggered whenever a function is added or updated.
    """
    print(f"Function '{triggered_function_name}' has been {action}.")
    function_data = func.get_function(triggered_function_name) if triggered_function_name else None
    if function_data:
        return triggered_function_name
    else:
        print(f"Function '{triggered_function_name}' not found in the database.")
        return None

@func.register_function(
    metadata={"description": "Add a secret key to the database."},
    imports=["os"]
)
def add_key_wrapper(key_name: str, key_value: str):
    return func.add_key(key_name, key_value)

@func.register_function(metadata={"description": "Get all versions of a given function."})
def get_function_versions_wrapper(name: str):
    return func.get_function_versions(name)

@func.register_function()
def get_function_wrapper(name: str):
    return func.get_function(name)


@func.register_function(metadata={"description": "Get all versions of a given function."})
def get_all_functions_wrapper():
    return func.get_all_functions()

@func.register_function(metadata={"description": "Activate a specific version of a function."})
def activate_function_version_wrapper(name: str, version: int):
    return func.activate_function_version(name, version)

@func.register_function(metadata={"description": "Display all registered functions and their metadata."})
def display_functions_wrapper():
    return func.display()

@func.register_function(
    metadata={"description": "Get logs for a specific function, optionally filtered by date."},
    imports=['datetime']
                       )
def get_logs_wrapper(function_name: str = None, start_date: datetime = None,
                 end_date: datetime = None):
    return func.get_logs(function_name, start_date, end_date)

@func.register_function(metadata={"description": "Add a trigger that executes a specific function when another function is executed."})
def add_trigger_wrapper(triggered_function_name: str, triggering_function_name: Optional[str] = None):
    return func.add_trigger(triggered_function_name, triggering_function_name)


@func.register_function(metadata={"description": "Get all secret keys stored."})
def get_all_secret_keys():
    return func.get_all_secret_keys()


@func.register_function(metadata={"description": "Get all imports."})
def get_all_imports_wrapper():
    return func.get_all_imports()