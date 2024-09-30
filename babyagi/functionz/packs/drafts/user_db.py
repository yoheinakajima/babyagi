# packs/user_db.py

from PythonFunc.core.framework import func

@func.register_function(
    metadata={"description": "Base UserDB class for database operations."},
    imports=["sqlalchemy", "contextlib"]
)
def get_user_db_class():
    from sqlalchemy import create_engine, Column, Integer, String, MetaData
    from sqlalchemy.ext.declarative import declarative_base
    from sqlalchemy.orm import sessionmaker
    from contextlib import contextmanager
    from sqlalchemy.exc import SQLAlchemyError

    class UserDB:
        def __init__(self, db_url='sqlite:///user_db.sqlite'):
            self.engine = create_engine(db_url)
            self.Session = sessionmaker(bind=self.engine)
            self.metadata = MetaData()
            self.Base = declarative_base(metadata=self.metadata)

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
                session.close()

    return UserDB.__name__  # Return the name of the class instead of the class itself

@func.register_function(
    metadata={"description": "Create a new database."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy"]
)
def create_database(db_name: str, db_type: str = 'sqlite', **kwargs):
    from sqlalchemy import create_engine, MetaData

    if db_type == 'sqlite':
        db_url = f'sqlite:///{db_name}.sqlite'
    elif db_type == 'postgresql':
        db_url = f'postgresql://{kwargs.get("user")}:{kwargs.get("password")}@{kwargs.get("host", "localhost")}:{kwargs.get("port", 5432)}/{db_name}'
    elif db_type == 'mysql':
        db_url = f'mysql+pymysql://{kwargs.get("user")}:{kwargs.get("password")}@{kwargs.get("host", "localhost")}:{kwargs.get("port", 3306)}/{db_name}'
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    UserDB_name = func.get_user_db_class()
    # Reconstruct the UserDB class
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })

    user_db = UserDB(db_url)  # Pass db_url here

    new_engine = create_engine(db_url)
    user_db.metadata.create_all(new_engine)
    return f"Database '{db_name}' created successfully."


@func.register_function(
    metadata={"description": "List all SQLite databases."},
    dependencies=["get_user_db_class"],
    imports=["os", "sqlalchemy"]
)
def list_databases():
    import os
    from sqlalchemy import create_engine, MetaData
    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })
    # This function doesn't actually use UserDB, but we include it for consistency
    return [f for f in os.listdir() if f.endswith('.sqlite')]

@func.register_function(
    metadata={"description": "Delete a database."},
    dependencies=["get_user_db_class"],
    imports=["os", "sqlalchemy"]
)
def delete_database(db_name: str, db_type: str = 'sqlite', **kwargs):
    import os
    from sqlalchemy import create_engine, MetaData
    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })
    # This function doesn't actually use UserDB, but we include it for consistency
    if db_type == 'sqlite':
        os.remove(f'{db_name}.sqlite')
        return f"Database '{db_name}' deleted successfully."
    else:
        raise NotImplementedError(f"Deleting {db_type} databases is not implemented yet.")

@func.register_function(
    metadata={"description": "Create a new table in the database."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy", "json"]  # Added 'json' to imports
)
def create_table(db_name: str, table_name: str, columns: str):
    from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Boolean, DateTime, LargeBinary
    import json  # Imported json within the function


    try:
        columns = json.loads(columns)
        print("Parsed columns:", columns)  # Debugging statement
    except json.JSONDecodeError as e:
        return f"Invalid JSON for columns: {e}"

    def get_column_type(type_name):
        type_map = {
            'string': String,
            'integer': Integer,
            'float': Float,
            'boolean': Boolean,
            'datetime': DateTime,
            'binary': LargeBinary,
            'embedding': LargeBinary  # We'll use LargeBinary for embeddings
        }
        return type_map.get(type_name.lower(), String)  # Default to String if type not found

    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData(),
    })
    user_db = UserDB(f'sqlite:///{db_name}.sqlite')

    # Create the table
    table = Table(
        table_name,
        user_db.metadata,
        Column('id', Integer, primary_key=True),
        *(Column(col['name'], get_column_type(col['type'])) for col in columns)
    )

    # Create the table in the database
    table.create(user_db.engine, checkfirst=True)

    return f"Table '{table_name}' created successfully in database '{db_name}'."



@func.register_function(
    metadata={"description": "List all tables in a database."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy"]
)
def list_tables(db_name: str):
    from sqlalchemy import create_engine, MetaData
    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })
    user_db = UserDB(f'sqlite:///{db_name}.sqlite')
    user_db.metadata.reflect(user_db.engine)
    return [table.name for table in user_db.metadata.tables.values()]

@func.register_function(
    metadata={"description": "Get details of a specific table."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy"]
)
def get_table(db_name: str, table_name: str):
    from sqlalchemy import create_engine, MetaData, Table
    from sqlalchemy.exc import NoSuchTableError

    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })

    try:
        user_db = UserDB(f'sqlite:///{db_name}.sqlite')
        user_db.metadata.reflect(user_db.engine)

        if table_name in user_db.metadata.tables:
            table = Table(table_name, user_db.metadata, autoload_with=user_db.engine)
            return {
                "name": table.name,
                "columns": [{"name": column.name, "type": str(column.type)} for column in table.columns]
            }
        else:
            return f"Table '{table_name}' not found in database '{db_name}'."
    except NoSuchTableError:
        return f"Table '{table_name}' not found in database '{db_name}'."
    except Exception as e:
        return f"Error getting table details: {str(e)}"
        
@func.register_function(
    metadata={"description": "Update a table by adding new columns."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy", "json"]  # Added 'json' to imports
)
def update_table(db_name: str, table_name: str, new_columns: str):
    from sqlalchemy import create_engine, MetaData, Table, Column, String, Integer, Float, Boolean, DateTime, LargeBinary
    from sqlalchemy.schema import CreateTable
    import json  # Imported json within the function

    try:
        new_columns = json.loads(new_columns)
        print("Parsed columns:", new_columns)  # Debugging statement
    except json.JSONDecodeError as e:
        return f"Invalid JSON for columns: {e}"

    def get_column_type(type_name):
        type_map = {
            'string': String,
            'integer': Integer,
            'float': Float,
            'boolean': Boolean,
            'datetime': DateTime,
            'binary': LargeBinary,
            'embedding': LargeBinary  # We'll use LargeBinary for embeddings
        }
        return type_map.get(type_name.lower(), String)  # Default to String if type not found


    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })

    try:
        user_db = UserDB(f'sqlite:///{db_name}.sqlite')
        user_db.metadata.reflect(user_db.engine)

        if table_name not in user_db.metadata.tables:
            return f"Table '{table_name}' not found in database '{db_name}'."

        table = Table(table_name, user_db.metadata, autoload_with=user_db.engine)
        existing_columns = set(column.name for column in table.columns)

        for col in new_columns:
            if col['name'] not in existing_columns:
                new_column = Column(col['name'], get_column_type(col['type']))
                # Generate the SQL statement to add the new column
                alter_stmt = f'ALTER TABLE {table_name} ADD COLUMN {new_column.name} {new_column.type}'
                user_db.engine.execute(alter_stmt)

        # Refresh the table metadata
        user_db.metadata.clear()
        user_db.metadata.reflect(user_db.engine)

        return f"Table '{table_name}' updated successfully in database '{db_name}'."

    except Exception as e:
        return f"An error occurred while updating the table: {e}"


@func.register_function(
    metadata={"description": "Delete a table from the database."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy"]
)
def delete_table(db_name: str, table_name: str):
    from sqlalchemy import create_engine, MetaData, Table
    from sqlalchemy.exc import NoSuchTableError

    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })

    try:
        user_db = UserDB(f'sqlite:///{db_name}.sqlite')
        user_db.metadata.reflect(user_db.engine)

        if table_name in user_db.metadata.tables:
            table = Table(table_name, user_db.metadata, autoload_with=user_db.engine)
            table.drop(user_db.engine)
            user_db.metadata.remove(table)
            return f"Table '{table_name}' deleted successfully from database '{db_name}'."
        else:
            return f"Table '{table_name}' not found in database '{db_name}'."
    except NoSuchTableError:
        return f"Table '{table_name}' not found in database '{db_name}'."
    except Exception as e:
        return f"Error deleting table: {str(e)}"


@func.register_function(
    metadata={"description": "Create a new record in a table."},
    dependencies=["get_user_db_class", "convert_value"],
    imports=["sqlalchemy", "json"]
)
def create_record(db_name: str, table_name: str, data: list):
    from sqlalchemy import create_engine, MetaData, Table, String
    from sqlalchemy.orm import sessionmaker
    import json

    if not isinstance(data_dict, dict):
        return "Error: Data must be a JSON object"

    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })
    user_db = UserDB(f'sqlite:///{db_name}.sqlite')
    user_db.metadata.reflect(user_db.engine)
    table = Table(table_name, user_db.metadata, autoload_with=user_db.engine)
    Session = sessionmaker(bind=user_db.engine)

    # Get column types
    column_types = {c.name: c.type for c in table.columns}

    # Convert input data to appropriate types
    converted_data = {key: func.convert_value(value, column_types.get(key, String)) for key, value in data.items()}

    try:
        with Session() as session:
            ins = table.insert().values(**converted_data)
            session.execute(ins)
            session.commit()
        return f"Record created in table '{table_name}' of database '{db_name}'."
    except Exception as e:
        return f"Error creating record: {str(e)}"
        
def read_records(db_name: str, table_name: str, filters: dict = None):
    from sqlalchemy import create_engine, MetaData, Table
    from sqlalchemy.orm import sessionmaker
    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })
    user_db = UserDB(f'sqlite:///{db_name}.sqlite')
    user_db.metadata.reflect(user_db.engine)
    table = Table(table_name, user_db.metadata, autoload_with=user_db.engine)
    Session = sessionmaker(bind=user_db.engine)
    with Session() as session:
        query = session.query(table)
        if filters:
            query = query.filter_by(**filters)
        return [dict(row) for row in query.all()]

@func.register_function(
    metadata={"description": "Update a record in a table."},
    dependencies=["get_user_db_class", "convert_value"],
    imports=["sqlalchemy", "json"]
)
def update_record(db_name: str, table_name: str, record_id: int, data: json):
    from sqlalchemy import create_engine, MetaData, Table, String
    from sqlalchemy.orm import sessionmaker
    import json

    if not isinstance(data_dict, dict):
        return "Error: Data must be a JSON object"

    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })
    user_db = UserDB(f'sqlite:///{db_name}.sqlite')
    user_db.metadata.reflect(user_db.engine)
    table = Table(table_name, user_db.metadata, autoload_with=user_db.engine)
    Session = sessionmaker(bind=user_db.engine)

    # Get column types
    column_types = {c.name: c.type for c in table.columns}

    # Convert input data to appropriate types
    converted_data = {key: func.convert_value(value, column_types.get(key, String)) for key, value in data.items()}

    try:
        with Session() as session:
            update = table.update().where(table.c.id == record_id).values(**converted_data)
            result = session.execute(update)
            session.commit()
            if result.rowcount:
                return f"Record {record_id} in table '{table_name}' of database '{db_name}' updated successfully."
            return f"Record {record_id} not found in table '{table_name}' of database '{db_name}'."
    except Exception as e:
        return f"Error updating record: {str(e)}"

@func.register_function(
    metadata={"description": "Delete a record from a table."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy"]
)
def delete_record(db_name: str, table_name: str, record_id: int):
    from sqlalchemy import create_engine, MetaData, Table
    from sqlalchemy.orm import sessionmaker
    UserDB_name = func.get_user_db_class()
    UserDB = type(UserDB_name, (), {
        '__init__': lambda self, db_url: setattr(self, 'engine', create_engine(db_url)),
        'metadata': MetaData()
    })
    user_db = UserDB(f'sqlite:///{db_name}.sqlite')
    user_db.metadata.reflect(user_db.engine)
    table = Table(table_name, user_db.metadata, autoload_with=user_db.engine)
    Session = sessionmaker(bind=user_db.engine)
    with Session() as session:
        delete = table.delete().where(table.c.id == record_id)
        result = session.execute(delete)
        session.commit()
        if result.rowcount:
            return f"Record {record_id} in table '{table_name}' of database '{db_name}' deleted successfully."
        return f"Record {record_id} not found in table '{table_name}' of database '{db_name}'."


@func.register_function(
    metadata={"description": "Convert value to specified SQLAlchemy type"},
    imports=["sqlalchemy", "json", "datetime"]
)
def convert_value(value, target_type):
    from sqlalchemy import Boolean, DateTime, LargeBinary, Integer, Float
    import json
    from datetime import datetime

    if isinstance(value, str):
        if target_type == Boolean:
            return value.lower() in ('true', 'yes', '1', 'on')
        elif target_type == DateTime:
            return datetime.fromisoformat(value)
        elif target_type == LargeBinary:
            try:
                # Assume it's a JSON array for embeddings
                return json.dumps(json.loads(value)).encode('utf-8')
            except json.JSONDecodeError:
                # If not JSON, treat as regular binary data
                return value.encode('utf-8')
        elif target_type in (Integer, Float):
            return target_type(value)
    return value  # Return as-is for String or if already correct type

@func.register_function(
    metadata={"description": "Create a new table in the database."},
    dependencies=["get_user_db_class"],
    imports=["sqlalchemy"]
)