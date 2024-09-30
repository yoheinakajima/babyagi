from typing import List, Optional, Dict, Any
from contextlib import contextmanager
from datetime import datetime

from .local_db import LocalDB
from .base_db import BaseDB
from .models import Import, Function, FunctionVersion, Log

class ImportResult:
    def __init__(self, name: str, source: str):
        self.name = name
        self.source = source

class DBRouter(BaseDB):
    def __init__(self, db_type: str = 'local', **kwargs):
        if db_type == 'local':
            self.db = LocalDB(**kwargs)
        else:
            raise ValueError(f"Unsupported database type: {db_type}")

    @contextmanager
    def session_scope(self):
        with self.db.session_scope() as session:
            yield session

    # Function management
    def add_function(self, name: str, code: str, metadata: Optional[Dict[str, Any]] = None, 
                     dependencies: Optional[List[str]] = None, 
                     triggers: Optional[List[str]] = None,
                     input_parameters: Optional[List[Dict[str, str]]] = None,
                     output_parameters: Optional[List[Dict[str, str]]] = None,
                     imports: Optional[List[str]] = None) -> None:
        with self.session_scope() as session:
            self.db.add_or_update_function(session, name, code, metadata, dependencies, triggers, input_parameters, output_parameters, imports)

    def update_function(self, name: str, code: Optional[str] = None, 
                        metadata: Optional[Dict[str, Any]] = None, 
                        dependencies: Optional[List[str]] = None,
                        triggers: Optional[List[str]] = None,
                        input_parameters: Optional[List[Dict[str, str]]] = None,
                        output_parameters: Optional[List[Dict[str, str]]] = None,
                        imports: Optional[List[str]] = None) -> None:
        with self.session_scope() as session:
            function = self.db.get_function(session, name)
            if function:
                active_version = self.db.get_active_version(session, function)
                self.db.add_or_update_function(
                    session, name, 
                    code if code is not None else active_version.code,
                    metadata or active_version.function_metadata,
                    dependencies, 
                    triggers if triggers is not None else active_version.triggers,
                    input_parameters or active_version.input_parameters,
                    output_parameters or active_version.output_parameters,
                    imports
                )

    def get_function(self, name: str) -> Optional[Dict[str, Any]]:
        with self.session_scope() as session:
            function = self.db.get_function(session, name)
            if function:
                active_version = self.db.get_active_version(session, function)
                if active_version:
                    return {
                        'name': function.name,
                        'version': active_version.version,
                        'code': active_version.code,
                        'metadata': active_version.function_metadata,
                        'dependencies': [dep.name for dep in active_version.dependencies],
                        'imports': [imp.name for imp in active_version.imports],
                        'created_date': active_version.created_date.isoformat(),
                        'input_parameters': active_version.input_parameters,
                        'output_parameters': active_version.output_parameters,
                        'triggers': active_version.triggers
                    }
            return None

    def get_all_functions(self) -> List[Dict[str, Any]]:
        with self.session_scope() as session:
            functions = self.db.get_all_functions(session)
            return [
                {
                    'name': function.name,
                    'version': active_version.version,
                    'code': active_version.code,
                    'metadata': active_version.function_metadata,
                    'dependencies': [dep.name for dep in active_version.dependencies],
                    'imports': [imp.name for imp in active_version.imports],
                    'created_date': active_version.created_date.isoformat(),
                    'input_parameters': active_version.input_parameters,
                    'output_parameters': active_version.output_parameters,
                    'triggers': active_version.triggers
                }
                for function in functions
                if (active_version := next((v for v in function.versions if v.is_active), None))
            ]

    def remove_function(self, name: str) -> None:
        with self.session_scope() as session:
            function = self.db.get_function(session, name)
            if function:
                session.delete(function)

    def get_function_versions(self, name: str) -> List[Dict[str, Any]]:
        with self.session_scope() as session:
            function = self.db.get_function(session, name)
            if function:
                return [
                    {
                        'version': v.version,
                        'code': v.code,
                        'metadata': v.function_metadata,
                        'is_active': v.is_active,
                        'dependencies': [dep.name for dep in v.dependencies],
                        'created_date': v.created_date.isoformat(),
                        'input_parameters': v.input_parameters,
                        'output_parameters': v.output_parameters,
                        'triggers': v.triggers
                    }
                    for v in function.versions
                ]
            return []

    def activate_function_version(self, name: str, version: int) -> None:
        with self.session_scope() as session:
            function = self.db.get_function(session, name)
            if function:
                for v in function.versions:
                    v.is_active = (v.version == version)

    # Import management
    def add_import(self, name: str, source: str, lib: Optional[str] = None) -> None:
        with self.session_scope() as session:
            self.db.add_import(session, name, source, lib)

    def get_all_imports(self) -> List[Dict[str, Any]]:
        with self.session_scope() as session:
            imports = session.query(Import).all()
            return [{"name": imp.name, "source": imp.source, "lib": imp.lib} for imp in imports]

    def get_function_imports(self, function_name: str) -> List[Dict[str, Any]]:
        with self.session_scope() as session:
            function = session.query(Function).filter_by(name=function_name).first()
            if function:
                imports = (session.query(Import)
                           .join(FunctionVersion.imports)
                           .filter(FunctionVersion.function_id == function.id)
                           .all())
                return [{"name": imp.name, "source": imp.source, "lib": imp.lib} for imp in imports]
            return []

    # Logging
    def add_log(self, function_name: str, message: str, timestamp: datetime, 
                params: Optional[Dict[str, Any]] = None, 
                output: Optional[Any] = None, 
                time_spent: Optional[float] = None, 
                parent_log_id: Optional[int] = None, 
                triggered_by_log_id: Optional[int] = None, 
                log_type: str = 'info') -> int:
        with self.session_scope() as session:
            return self.db.add_log(
                session=session,
                function_name=function_name,
                message=message,
                timestamp=timestamp,
                params=params,
                output=output,
                time_spent=time_spent,
                parent_log_id=parent_log_id,
                triggered_by_log_id=triggered_by_log_id,
                log_type=log_type
            )

    def update_log(self, log_id: int, **kwargs) -> None:
        with self.session_scope() as session:
            self.db.update_log(
                session=session,
                log_id=log_id,
                **kwargs
            )


    def update_log_params(self, log_id: int, params: Dict[str, Any]) -> None:
        with self.session_scope() as session:
            self.db.update_log_params(
                session=session,
                log_id=log_id,
                params=params
            )



    def get_logs(self, function_name: Optional[str] = None, 
                 start_date: Optional[datetime] = None, 
                 end_date: Optional[datetime] = None, 
                 triggered_by_log_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with self.session_scope() as session:
            logs = self.db.get_logs(session, function_name, start_date, end_date, triggered_by_log_id)
            return [
                {
                    'id': log.id,
                    'function_name': log.function_name,
                    'message': log.message,
                    'timestamp': log.timestamp.isoformat(),
                    'params': log.params,
                    'output': log.output,
                    'time_spent': log.time_spent,
                    'parent_log_id': log.parent_log_id,
                    'triggered_by_log_id': log.triggered_by_log_id,
                    'log_type': log.log_type
                }
                for log in logs
            ]

    def get_log_bundle(self, log_id: int) -> List[Dict[str, Any]]:
        with self.session_scope() as session:
            logs_collected = {}

            def fetch_related_logs(current_log_id):
                if current_log_id in logs_collected:
                    return
                log = self.db.get_log(session, current_log_id)
                if log:
                    logs_collected[current_log_id] = log
                else:
                    logger.warning(f"Log ID {current_log_id} not found.")
                    return

                # Fetch parent log
                if log.parent_log_id:
                    fetch_related_logs(log.parent_log_id)

                    # Fetch sibling logs
                    sibling_logs = session.query(Log).filter(
                        Log.parent_log_id == log.parent_log_id,
                        Log.id != current_log_id
                    ).all()
                    for sibling in sibling_logs:
                        fetch_related_logs(sibling.id)

                # Fetch child logs
                child_logs = self.db.get_child_logs(session, current_log_id)
                for child in child_logs:
                    fetch_related_logs(child.id)

            fetch_related_logs(log_id)

            # Convert logs to dictionaries
            all_logs = [
                {
                    'id': log.id,
                    'function_name': log.function_name,
                    'message': log.message,
                    'timestamp': log.timestamp.isoformat(),
                    'params': log.params,
                    'output': log.output,
                    'time_spent': log.time_spent,
                    'parent_log_id': log.parent_log_id,
                    'triggered_by_log_id': log.triggered_by_log_id,
                    'log_type': log.log_type
                }
                for log in logs_collected.values()
            ]

            return all_logs


    
    # Secret key management
    def add_secret_key(self, key_name: str, key_value: str) -> None:
        with self.session_scope() as session:
            existing_key = self.db.get_secret_key(session, key_name)
            if existing_key:
                existing_key.value = key_value
            else:
                self.db.add_secret_key(session, key_name, key_value)

    def get_secret_key(self, key_name: str) -> Optional[str]:
        with self.session_scope() as session:
            secret_key = self.db.get_secret_key(session, key_name)
            return secret_key.value if secret_key else None

    def get_all_secret_keys(self) -> Dict[str, str]:
        with self.session_scope() as session:
            secret_keys = self.db.get_all_secret_keys(session)
            return {key.name: key.value for key in secret_keys if key.value is not None}

    # Trigger management
    def add_trigger(self, triggered_function_name: str, triggering_function_name: Optional[str] = None) -> None:
        with self.session_scope() as session:
            self.db.add_trigger(session, triggered_function_name, triggering_function_name)

    def get_triggers_for_function(self, function_name: str) -> List[str]:
        with self.session_scope() as session:
            all_functions = self.db.get_all_functions(session)
            triggered_functions = []
            for func in all_functions:
                active_version = self.db.get_active_version(session, func)
                if active_version and active_version.triggers:
                    if function_name in active_version.triggers:
                        triggered_functions.append(func.name)
            return triggered_functions