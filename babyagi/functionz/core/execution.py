import subprocess
import sys
import importlib
import inspect
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class FunctionExecutor:
    def __init__(self, python_func):
        self.python_func = python_func

    def _install_external_dependency(self, package_name: str, imp_name: str) -> Any:
        try:
            return importlib.import_module(imp_name)
        except ImportError:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
            return importlib.import_module(package_name)

    def _resolve_dependencies(self, function_version: Dict[str, Any], local_scope: Dict[str, Any],
                              parent_log_id: Optional[int], executed_functions: List[str],
                              visited: Optional[set] = None) -> None:
        if visited is None:
            visited = set()

        function_name = function_version['name']
        function_imports = self.python_func.db.get_function_imports(function_name)

        for imp in function_imports:
            lib_name = imp['lib'] if imp['lib'] else imp['name']
            if lib_name not in local_scope:
                module = self._install_external_dependency(lib_name, imp['name'])
                local_scope[imp['name']] = module

        for dep_name in function_version.get('dependencies', []):
            if dep_name not in local_scope and dep_name not in visited:
                visited.add(dep_name)
                dep_data = self.python_func.db.get_function(dep_name)
                if not dep_data:
                    raise ValueError(f"Dependency '{dep_name}' not found in the database.")
                self._resolve_dependencies(dep_data, local_scope, parent_log_id, executed_functions, visited)
                exec(dep_data['code'], local_scope)
                if dep_name in local_scope:
                    dep_func = local_scope[dep_name]
                    # Wrap the dependent function
                    local_scope[dep_name] = self._create_function_wrapper(dep_func, dep_name, parent_log_id, executed_functions)

    def _create_function_wrapper(self, func: callable, func_name: str, parent_log_id: int, executed_functions: List[str]):
        def wrapper(*args, **kwargs):
            return self.execute(func_name, *args, executed_functions=executed_functions, parent_log_id=parent_log_id, **kwargs)
        return wrapper

    def execute(
        self,
        function_name: str,
        *args,
        executed_functions: Optional[List[str]] = None,
        parent_log_id: Optional[int] = None,
        wrapper_log_id: Optional[int] = None,
        triggered_by_log_id: Optional[int] = None,
        **kwargs
    ) -> Any:
        start_time = datetime.now()
        executed_functions = executed_functions or []
        log_id = None
        bound_args = None
        output = None

        # Ensure wrapper_log_id is initialized
        wrapper_log_id = wrapper_log_id if wrapper_log_id is not None else None

        logger.info(f"Executing function: {function_name}")

        try:
            executed_functions.append(function_name)
            function_version = self.python_func.db.get_function(function_name)
            if not function_version:
                raise ValueError(f"Function '{function_name}' not found in the database.")

            # If the function being executed is the wrapper, create a special log entry and set wrapper_log_id
            if function_name == 'execute_function_wrapper':
                log_id = self._add_execution_log(
                    function_name,
                    start_time,
                    {},
                    None,
                    0,
                    parent_log_id,
                    triggered_by_log_id,
                    'started'
                )
                wrapper_log_id = log_id
            else:
                log_id = self._add_execution_log(
                    function_name,
                    start_time,
                    {},
                    None,
                    0,
                    wrapper_log_id if wrapper_log_id else parent_log_id,
                    triggered_by_log_id,
                    'started'
                )

            # Include 'datetime' in local_scope
            local_scope = {
                'func': self.python_func,
                'parent_log_id': log_id,
                'datetime': datetime  # Added datetime here
            }

            self._resolve_dependencies(
                function_version,
                local_scope,
                parent_log_id=log_id,
                executed_functions=executed_functions
            )
            self._inject_secret_keys(local_scope)

            exec(function_version['code'], local_scope)
            if function_name not in local_scope:
                raise ValueError(f"Failed to load function '{function_name}'.")

            func = local_scope[function_name]
            bound_args = self._bind_function_arguments(func, args, kwargs)
            self._validate_input_parameters(function_version, bound_args)

            params = bound_args.arguments
            self._update_execution_log_params(log_id, params)

            output = func(*bound_args.args, **bound_args.kwargs)
            end_time = datetime.now()
            time_spent = (end_time - start_time).total_seconds()

            self._update_execution_log(log_id, output, time_spent, 'success')

            # Check and execute triggers for the function
            self._execute_triggered_functions(function_name, output, executed_functions, log_id)
            return output

        except Exception as e:
            end_time = datetime.now()
            time_spent = (end_time - start_time).total_seconds()
            if log_id is not None:
                self._update_execution_log(log_id, None, time_spent, 'error', str(e))
            raise

    

    def _check_key_dependencies(self, function_version: Dict[str, Any]) -> None:
        if 'key_dependencies' in function_version.get('metadata', {}):
            for key_name in function_version['metadata']['key_dependencies']:
                if key_name not in self.python_func.db.get_all_secret_keys():
                    raise ValueError(f"Required secret key '{key_name}' not found for function '{function_version['name']}'")

    def _inject_secret_keys(self, local_scope: Dict[str, Any]) -> None:
        secret_keys = self.python_func.db.get_all_secret_keys()
        if secret_keys:
            logger.debug(f"Injecting secret keys: {list(secret_keys.keys())}")
            local_scope.update(secret_keys)

    def _bind_function_arguments(self, func: callable, args: tuple, kwargs: dict) -> inspect.BoundArguments:
        sig = inspect.signature(func)
        bound_args = sig.bind(*args, **kwargs)
        bound_args.apply_defaults()
        return bound_args

    def _validate_input_parameters(self, function_version: Dict[str, Any], bound_args: inspect.BoundArguments) -> None:
        input_params = function_version.get('input_parameters', [])
        for param in input_params:
            if param['name'] not in bound_args.arguments:
                raise ValueError(f"Missing required input parameter '{param['name']}' for function '{function_version['name']}'")

    def _add_execution_log(self, function_name: str, start_time: datetime, params: Dict[str, Any],
                           output: Any, time_spent: float, parent_log_id: Optional[int],
                           triggered_by_log_id: Optional[int], log_type: str, error_message: Optional[str] = None) -> int:
        if log_type == 'started':
            message = "Execution started."
        elif log_type == 'success':
            message = "Execution successful."
        else:
            message = f"Execution failed. Error: {error_message}"
        return self.python_func.db.add_log(
            function_name=function_name,
            message=message,
            timestamp=start_time,
            params=params,
            output=output,
            time_spent=time_spent,
            parent_log_id=parent_log_id,
            triggered_by_log_id=triggered_by_log_id,
            log_type=log_type
        )

    def _update_execution_log(self, log_id: int, output: Any, time_spent: float, log_type: str,
          error_message: Optional[str] = None):
        message = "Execution successful." if log_type == 'success' else f"Execution failed. Error: {error_message}"
        update_data = {
            'message': message,
            'log_type': log_type
        }
        if output is not None:
            update_data['output'] = output
        if time_spent is not None:
            update_data['time_spent'] = time_spent

            self.python_func.db.update_log(log_id=log_id, **update_data)


    def _update_execution_log_params(self, log_id: int, params: Dict[str, Any]) -> None:
        self.python_func.db.update_log(log_id=log_id, params=params)


    
    def _execute_triggered_functions(self, function_name: str, output: Any, executed_functions: List[str], log_id: int) -> None:
        triggered_function_names = self.python_func.db.get_triggers_for_function(function_name)
        logger.info(f"Functions triggered by {function_name}: {triggered_function_names}")

        for triggered_function_name in triggered_function_names:
            if triggered_function_name in executed_functions:
                logger.warning(f"Triggered function '{triggered_function_name}' already executed in this chain. Skipping to prevent recursion.")
                continue

            try:
                logger.info(f"Preparing to execute trigger: {triggered_function_name}")
                triggered_function = self.python_func.db.get_function(triggered_function_name)
                if triggered_function:
                    trigger_args, trigger_kwargs = self._prepare_trigger_arguments(triggered_function, output)
                    logger.info(f"Executing trigger {triggered_function_name} with args: {trigger_args} and kwargs: {trigger_kwargs}")

                    trigger_output = self.execute(
                        triggered_function_name,
                        *trigger_args,
                        executed_functions=executed_functions.copy(),
                        parent_log_id=log_id,
                        triggered_by_log_id=log_id,
                        **trigger_kwargs
                    )
                    logger.info(f"Trigger {triggered_function_name} execution completed. Output: {trigger_output}")
                else:
                    logger.error(f"Triggered function '{triggered_function_name}' not found in the database.")
            except Exception as e:
                logger.error(f"Error executing triggered function '{triggered_function_name}': {str(e)}")

    def _prepare_trigger_arguments(self, triggered_function: Dict[str, Any], output: Any) -> tuple:
        triggered_params = triggered_function.get('input_parameters', [])
        if triggered_params:
            # If the triggered function expects parameters, pass the output as the first parameter
            return (output,), {}
        else:
            # If the triggered function doesn't expect parameters, don't pass any
            return (), {}
