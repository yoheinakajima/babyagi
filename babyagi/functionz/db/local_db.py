# local_db.py

from sqlalchemy import create_engine, or_
from sqlalchemy.orm import sessionmaker, scoped_session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from .models import Base, Function, FunctionVersion, Import, Log, SecretKey, fernet
import datetime



class LocalDB:
    def __init__(self, db_path='sqlite:///funztionz.db'):
        self.engine = create_engine(db_path)
        Base.metadata.create_all(self.engine)
        self.Session = scoped_session(sessionmaker(bind=self.engine))

    @contextmanager
    def session_scope(self):
        session = self.Session()
        try:
            yield session
            session.commit()
        except SQLAlchemyError as e:
            session.rollback()
            raise e
        finally:
            self.Session.remove()

    def serialize_for_json(self, obj):
        """
        Recursively convert datetime objects to ISO format strings within the given object.
        Handles dictionaries, lists, and individual datetime objects.
        """
        if isinstance(obj, dict):
            return {k: self.serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self.serialize_for_json(element) for element in obj]
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        else:
            return obj


    def get_function(self, session, name):
        return session.query(Function).filter_by(name=name).first()

    def get_active_version(self, session, function):
        return session.query(FunctionVersion).filter_by(function_id=function.id, is_active=True).options(
            joinedload(FunctionVersion.dependencies)
        ).first()

    def get_all_functions(self, session):
        return session.query(Function).options(
            joinedload(Function.versions).joinedload(FunctionVersion.dependencies)
        ).all()

    def add_or_update_function(self, session, name, code, metadata, dependencies, triggers, input_parameters, output_parameters, imports=None):
        function = self.get_function(session, name)
        if not function:
            function = Function(name=name)
            session.add(function)
            session.flush()

        # Handle imports before creating the FunctionVersion
        import_objects = []
        if imports:
            for import_name in imports:
                imp = session.query(Import).filter_by(name=import_name).first()
                if not imp:
                    imp = Import(name=import_name, source='external')
                    session.add(imp)
                    session.flush()
                import_objects.append(imp)

        # Create the FunctionVersion instance, now including triggers as JSON
        version = FunctionVersion(
            function=function,
            version=len(function.versions) + 1,
            code=code,
            function_metadata=metadata or {},
            is_active=True,
            input_parameters=input_parameters or [],
            output_parameters=output_parameters or [],
            imports=import_objects,  # Pass the list of Import objects here
            triggers=triggers or []  # Store the triggers as JSON
        )
        session.add(version)

        # Handle dependencies
        if dependencies:
            for dep in dependencies:
                dep_func = self.get_function(session, dep)
                if dep_func:
                    version.dependencies.append(dep_func)

        # Deactivate previous versions
        for v in function.versions:
            if v != version:
                v.is_active = False


    def add_import(self, session, name, source, lib=None):
        existing_import = session.query(Import).filter_by(name=name).first()
        if not existing_import:
            new_import = Import(name=name, source=source, lib=lib)
            session.add(new_import)



    def add_log(self, session, function_name, message, timestamp, params, output, time_spent, parent_log_id=None, triggered_by_log_id=None, log_type='info'):
        if isinstance(timestamp, str):
            # Convert the string timestamp back to a datetime object
            timestamp = datetime.datetime.fromisoformat(timestamp)

        # Serialize params and output to ensure JSON serializability
        serialized_params = self.serialize_for_json(params) if params else None
        serialized_output = self.serialize_for_json(output) if output else None

        new_log = Log(
            function_name=function_name,
            message=message,
            timestamp=timestamp,
            params=serialized_params,
            output=serialized_output,
            time_spent=time_spent,
            parent_log_id=parent_log_id,
            triggered_by_log_id=triggered_by_log_id,
            log_type=log_type
        )
        session.add(new_log)
        session.flush()  # This ensures new_log.id is populated
        return new_log.id

    def update_log(self, session, log_id: int, **kwargs) -> None:
        # Fetch the log entry by id
        log_entry = session.query(Log).filter(Log.id == log_id).first()
        if log_entry:
            # Update only the fields provided in kwargs
            for key, value in kwargs.items():
                if hasattr(log_entry, key):
                    setattr(log_entry, key, value)
                else:
                    raise ValueError(f"Log has no attribute '{key}'")
            # No need to call session.commit(); it will be committed in the session scope
        else:
            raise ValueError(f"Log with id {log_id} not found.")



    def update_log_params(self, session, log_id: int, params) -> None:
        log_entry = session.query(Log).filter_by(id=log_id).one_or_none()
        if log_entry is None:
            raise ValueError(f"Log entry with id {log_id} not found.")

        log_entry.params = params
        session.commit()



    def get_log(self, session, log_id: int):
        """
        Fetches a single log entry by its ID.

        :param session: SQLAlchemy session object.
        :param log_id: The ID of the log to retrieve.
        :return: Log object if found, else None.
        """
        return session.query(Log).filter_by(id=log_id).first()

    def get_child_logs(self, session, parent_id: int):
        """
        Retrieves all child logs that have the given parent_log_id.

        :param session: SQLAlchemy session object.
        :param parent_id: The ID of the parent log.
        :return: List of Log objects.
        """
        return session.query(Log).filter_by(parent_log_id=parent_id).all()
    
    def get_logs(self, session, function_name=None, start_date=None, end_date=None, triggered_by_log_id=None):
        query = session.query(Log)

        if function_name:
            query = query.filter(Log.function_name == function_name)

        if start_date:
            query = query.filter(Log.timestamp >= start_date)

        if end_date:
            query = query.filter(Log.timestamp <= end_date)

        if triggered_by_log_id:
            query = query.filter(Log.triggered_by_log_id == triggered_by_log_id)

        return query.all()


    def get_log_bundle(self, session, log_id):
        logs_collected = {}

        def fetch_related_logs(current_log_id):
            if current_log_id in logs_collected:
                return
            log = session.query(Log).filter_by(id=current_log_id).one_or_none()
            if not log:
                return
            logs_collected[current_log_id] = log

            # Fetch parent log
            if log.parent_log_id:
                fetch_related_logs(log.parent_log_id)

                # Fetch sibling logs
                sibling_logs = session.query(Log).filter(
                    Log.parent_log_id == log.parent_log_id,
                    Log.id != current_log_id
                ).all()
                for sibling in sibling_logs:
                    if sibling.id not in logs_collected:
                        fetch_related_logs(sibling.id)

            # Fetch child logs
            child_logs = session.query(Log).filter_by(parent_log_id=current_log_id).all()
            for child in child_logs:
                if child.id not in logs_collected:
                    fetch_related_logs(child.id)

        fetch_related_logs(log_id)
        return list(logs_collected.values())




    def add_secret_key(self, session, function_id, key_name, key_value):
        print(f"Encrypting value for key '{key_name}'")
        try:
            encrypted_value = fernet.encrypt(key_value.encode())
            print(f"Value encrypted successfully for key '{key_name}'")
            secret_key = SecretKey(function_id=function_id, name=key_name, _encrypted_value=encrypted_value)
            session.add(secret_key)
            print(f"Secret key '{key_name}' added to session")
        except Exception as e:
            print(f"Error in add_secret_key: {str(e)}")
            raise

    
    def add_secret_key(self, session, key_name, key_value):
        encrypted_value = fernet.encrypt(key_value.encode())
        secret_key = SecretKey(name=key_name, _encrypted_value=encrypted_value)
        session.add(secret_key)

    def get_secret_key(self, session, key_name):
        return session.query(SecretKey).filter_by(name=key_name).first()

    
    def get_all_secret_keys(self, session):
        return session.query(SecretKey).all()

    