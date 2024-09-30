# core/framework.py

import os
import sys
import importlib.util
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..db.db_router import DBRouter
from .execution import FunctionExecutor
from .registration import FunctionRegistrar

logger = logging.getLogger(__name__)

class Functionz:
    def __init__(self, db_type='local', **db_kwargs):
        self.db = DBRouter(db_type, **db_kwargs)
        self.executor = FunctionExecutor(self)
        self.registrar = FunctionRegistrar(self)

    # Function execution
    def execute_function(self, function_name: str, *args, **kwargs):
        return self.executor.execute(function_name, *args, **kwargs)

    def __getattr__(self, name):
        if self.db.get_function(name):
            return lambda *args, **kwargs: self.executor.execute(name, *args, **kwargs)
        raise AttributeError(f"'PythonFunc' object has no attribute '{name}'")

    # Function management
    def get_function(self, name: str):
        return self.db.get_function(name)

    def get_function_versions(self, name: str):
        return self.db.get_function_versions(name)

    def get_all_functions(self) -> List[Dict[str, Any]]:
        return self.db.get_all_functions()

    def activate_function_version(self, name: str, version: int) -> None:
        self.db.activate_function_version(name, version)

    def get_function_imports(self, name: str):
        return self.db.get_function_imports(name)

    # Function registration (exposing registrar methods)
    def register_function(self, *args, **kwargs):
        return self.registrar.register_function(*args, **kwargs)

    def update_function(self, *args, **kwargs):
        return self.registrar.update_function(*args, **kwargs)

    def add_function(self, *args, **kwargs):
        return self.registrar.add_function(*args, **kwargs)

    # Key management
    def add_key(self, key_name: str, key_value: str) -> None:
        self.db.add_secret_key(key_name, key_value)

    def get_all_secret_keys(self, *args, **kwargs):
        return self.db.get_all_secret_keys(*args, **kwargs)

    # Import management
    def get_all_imports(self, *args, **kwargs):
        return self.db.get_all_imports(*args, **kwargs)

    # Function pack and file loading
    def load_function_pack(self, pack_name: str):
        packs_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'packs')
        pack_path = os.path.join(packs_dir, pack_name + '.py')

        if not os.path.exists(pack_path):
            logger.error(f"Function pack '{pack_name}' not found.")
            return

        self._load_module_from_path(pack_path, pack_name)

    def load_functions_from_file(self, file_path: str):
        if not os.path.exists(file_path):
            logger.error(f"File '{file_path}' not found.")
            return

        module_name = os.path.splitext(os.path.basename(file_path))[0]
        self._load_module_from_path(file_path, module_name)

    def _load_module_from_path(self, path: str, module_name: str):
        spec = importlib.util.spec_from_file_location(module_name, path)
        module = importlib.util.module_from_spec(spec)
        module.func = self

        original_sys_path = sys.path[:]
        try:
            babyagi_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
            if babyagi_root not in sys.path:
                sys.path.insert(0, babyagi_root)

            spec.loader.exec_module(module)
            logger.info(f"Loaded module '{module_name}' from '{path}'")
        except Exception as e:
            logger.error(f"Error loading module '{module_name}' from '{path}': {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
        finally:
            sys.path = original_sys_path

    # Trigger management
    def add_trigger(self, triggered_function_name, triggering_function_name=None):
        self.db.add_trigger(triggered_function_name, triggering_function_name)

    def get_triggers_for_function(self, function_name: str) -> List[str]:
        function_data = self.get_function(function_name)
        return function_data.get('triggers', []) if function_data else []

    # Logging and display
    def get_logs(self, function_name: Optional[str] = None,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        return self.db.get_logs(function_name, start_date, end_date)

    def display(self):
        functions = self.db.get_all_functions()
        result = []

        for function in functions:
            function_info = [
                f"Function: {function['name']}",
                f"  Version: {function['version']}",
                f"  Created Date: {function['created_date']}",
                f"  Metadata: {function['metadata']}",
                f"  Dependencies: {function['dependencies']}",
                f"  Triggers: {function.get('triggers', [])}",
                "  Input Parameters:",
            ]
            for param in function['input_parameters']:
                function_info.append(f"    - {param['name']} ({param['type']})")

            function_info.append("  Output Parameters:")
            for param in function['output_parameters']:
                function_info.append(f"    - {param['name']} ({param['type']})")

            function_info.append(f"  Code:\n{function['code']}")
            function_info.append("---")

            result.append("\n".join(function_info))

        return "\n\n".join(result)

# Create the global 'func' instance
func = Functionz()