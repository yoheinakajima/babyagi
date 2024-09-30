# core/registration.py

from .execution import FunctionExecutor
import inspect
import ast
from typing import Optional, List, Dict, Any, Union
import logging
import json

logger = logging.getLogger(__name__)

class FunctionRegistrar:
    def __init__(self, python_func):
        self.python_func = python_func

    def register_function(self, metadata: Optional[Dict[str, Any]] = None,
                          imports: Optional[List[str]] = None,
                          dependencies: Optional[List[str]] = None,
                          triggers: Optional[List[str]] = None,
                          key_dependencies: Optional[List[str]] = None):
        """Decorator to register a function."""
        def decorator(func):
            function_name = func.__name__
            source_lines = inspect.getsourcelines(func)[0]
            func_start = next(i for i, line in enumerate(source_lines) if line.strip().startswith('def '))
            function_code = ''.join(source_lines[func_start:]).strip()

            # Store metadata on the function object
            func.__pythonfunc_metadata__ = {
                'metadata': metadata or {},
                'imports': imports or [],
                'dependencies': dependencies or [],
                'triggers': triggers or [], 
                'key_dependencies': key_dependencies or []
            }

            self.add_function(function_name, metadata=metadata, code=function_code,
                              imports=imports, dependencies=dependencies, 
                              key_dependencies=key_dependencies, triggers=triggers)
            def wrapper(*args, **kwargs):
                return self.python_func.executor.execute(function_name, *args, **kwargs)
            return wrapper
        return decorator

    def parse_function_parameters(self, code: str):
        """
        Parse the input and output parameters of a given function code.
        """
        try:
            # Parse the source code into an AST
            tree = ast.parse(code)

            # Find the function definition node
            function_def = next(node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef))

            # Parse input parameters
            input_params = []
            for arg in function_def.args.args:
                param_type = 'Any'
                if arg.annotation:
                    param_type = ast.unparse(arg.annotation)
                input_params.append({'name': arg.arg, 'type': param_type})

            # Parse return statement to identify output parameters
            output_params = []
            returns = [node for node in ast.walk(function_def) if isinstance(node, ast.Return)]
            if returns:
                return_node = returns[0].value
                if isinstance(return_node, ast.Dict):
                    # If returning a dictionary, treat each key as an output parameter
                    for key in return_node.keys:
                        if isinstance(key, ast.Str):
                            output_params.append({'name': key.s, 'type': 'Any'})
                elif isinstance(return_node, (ast.Name, ast.Attribute)):
                    # If returning a single variable
                    output_params.append({'name': 'output', 'type': 'Any'})
                elif isinstance(return_node, ast.Str):
                    # If returning a string literal
                    output_params.append({'name': 'output', 'type': 'str'})
                else:
                    # For other types of returns, use a generic 'output' parameter
                    output_params.append({'name': 'output', 'type': 'Any'})

            return input_params, output_params
        except Exception as e:
            # print(f"Error parsing function parameters: {str(e)}")
            return [], []

    def parse_import(self, imp):
        try:
            #print("Attempt to parse the string as JSON")
            #print(imp.type())
            parsed = json.loads(imp)
            #print("Parsed string as JSON")
            return parsed
        except json.JSONDecodeError:
            print("Failed to parse the string as JSON")
            # If it fails, return the original string (it's a simple import)
            return imp

    # Register imports helper function
    def register_imports(self, imports):
        print(f"Registering imports: {imports}")
        if isinstance(imports, list):
            for imp in imports:
                self.process_single_import(imp)
        elif isinstance(imports, dict):
            self.process_single_import(imports)

    def process_single_import(self, imp):
        if isinstance(imp, str):
            self.python_func.db.add_import(imp, 'external', lib=None)
        elif isinstance(imp, dict):
            name = imp.get('name')
            lib = imp.get('lib')
            if name:
                self.python_func.db.add_import(name, 'external', lib=lib)
        else:
            print(f"Unsupported import format: {imp}")

    def process_imports(self, imports):
        import_names = []
        if imports:
            if isinstance(imports, list):
                for imp in imports:
                    if isinstance(imp, str):
                        import_names.append(imp)
                    elif isinstance(imp, dict):
                        import_name = imp.get('name')
                        if import_name:
                            import_names.append(import_name)
            elif isinstance(imports, dict):
                import_name = imports.get('name')
                if import_name:
                    import_names.append(import_name)
        return import_names

    def function_has_no_changes(self, name, code, metadata, import_names, dependencies, triggers):
        existing_function = self.python_func.db.get_function(name)
        if not existing_function:
            return False  # Function does not exist, so changes are needed

        existing_code = existing_function.get('code')
        existing_metadata = existing_function.get('metadata', {})
        existing_description = existing_metadata.get('description')
        existing_imports = existing_function.get('imports') or []
        existing_dependencies = existing_function.get('dependencies') or []
        existing_triggers = existing_function.get('triggers') or []

        new_description = metadata.get('description') if metadata else None

        if (existing_code == code and
            existing_description == new_description and
            set(existing_imports) == set(import_names) and
            set(existing_dependencies) == set(dependencies) and
            set(existing_triggers) == set(triggers)):
            return True  # No changes
        else:
            return False  # Changes detected

    def add_function(self, name: str, metadata: Optional[Dict[str, Any]] = None,
                    code: Optional[str] = None, imports: Optional[List[Union[str, Dict[str, str]]]] = None,
                    dependencies: Optional[List[str]] = None, triggers: Optional[List[str]] = None,
                    key_dependencies: Optional[List[str]] = None,
                    input_parameters: Optional[List[Dict[str, str]]] = None,
                    output_parameters: Optional[List[Dict[str, str]]] = None) -> None:

        if code:
            # Parse input and output parameters if not provided
            if input_parameters is None or output_parameters is None:
                parsed_input, parsed_output = self.parse_function_parameters(code)
                input_parameters = input_parameters or parsed_input
                output_parameters = output_parameters or parsed_output

        # Process imports
        import_names = self.process_imports(imports)

        # Ensure lists are not None
        dependencies = dependencies or []
        triggers = triggers or []

        # Check for changes
        if self.function_has_no_changes(name, code, metadata, import_names, dependencies, triggers):
            #print(f"Function {name} has no changes.")
            return

        # Register imports
        if imports:
            self.register_imports(imports)

        # Add or update the function in the database
        existing_function = self.python_func.db.get_function(name)
        if existing_function:
            # Function exists, update it
            self.python_func.db.update_function(
                name, code=code, metadata=metadata, dependencies=dependencies,
                input_parameters=input_parameters, output_parameters=output_parameters,
                imports=import_names, triggers=triggers
            )
        else:
            # Function does not exist, add it
            self.python_func.db.add_function(
                name, code=code, metadata=metadata, dependencies=dependencies,
                input_parameters=input_parameters, output_parameters=output_parameters,
                imports=import_names, triggers=triggers
            )

        if key_dependencies:
            print(f"Function {name} requires keys: {key_dependencies}")
            metadata = metadata or {}
            metadata['key_dependencies'] = key_dependencies

        if self.python_func.db.get_function('function_added_or_updated'):
            try:
                action = 'updated' if existing_function else 'added'
                self.python_func.executor.execute(function_name='function_added_or_updated', action=action, triggered_function_name=name)
            except Exception as e:
                logger.error(f"Error executing trigger function 'function_added_or_updated': {str(e)}")

    def update_function(self, name: str, code: Optional[str] = None, imports: Optional[List[Union[str, Dict[str, str]]]] = None,
                        metadata: Optional[Dict[str, Any]] = None,
                        dependencies: Optional[List[str]] = None,
                        triggers: Optional[List[str]] = None,
                        key_dependencies: Optional[List[str]] = None,
                        input_parameters: Optional[List[Dict[str, str]]] = None,
                        output_parameters: Optional[List[Dict[str, str]]] = None) -> None:

        if code:
            # Parse input and output parameters if not provided
            if input_parameters is None or output_parameters is None:
                parsed_input, parsed_output = self.parse_function_parameters(code)
                input_parameters = input_parameters or parsed_input
                output_parameters = output_parameters or parsed_output

        # Process imports
        import_names = self.process_imports(imports)

        # Ensure lists are not None
        dependencies = dependencies or []
        triggers = triggers or []

        # Check for changes
        if self.function_has_no_changes(name, code, metadata, import_names, dependencies, triggers):
            # print(f"Function {name} has no changes.")
            return

        # Update the function in the database
        self.python_func.db.update_function(
            name, code=code, metadata=metadata, dependencies=dependencies,
            input_parameters=input_parameters, output_parameters=output_parameters,
            imports=import_names, triggers=triggers
        )

        if key_dependencies:
            metadata = metadata or {}
            metadata['key_dependencies'] = key_dependencies

        # Register imports
        if imports:
            self.register_imports(imports)

        if self.python_func.db.get_function('function_added_or_updated'):
            try:
                self.python_func.executor.execute(function_name='function_added_or_updated', action='updated', triggered_function_name=name)
            except Exception as e:
                logger.error(f"Error executing trigger function 'function_added_or_updated': {str(e)}")
