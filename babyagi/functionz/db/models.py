# models.py

from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey, Boolean, Table, Float, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from cryptography.fernet import Fernet
from cryptography.fernet import InvalidToken
from sqlalchemy.ext.hybrid import hybrid_property
import os
import json
from datetime import datetime

Base = declarative_base()

KEY_FILE = 'encryption_key.json'

def get_or_create_key():
    if os.path.exists(KEY_FILE):
        with open(KEY_FILE, 'r') as f:
            return json.load(f)['key']
    else:
        key = Fernet.generate_key().decode()
        with open(KEY_FILE, 'w') as f:
            json.dump({'key': key}, f)
        return key

ENCRYPTION_KEY = get_or_create_key()
print(f"Using encryption key: {ENCRYPTION_KEY}")
fernet = Fernet(ENCRYPTION_KEY.encode())

# Association table for function dependencies (many-to-many between FunctionVersion and Function)
function_dependency = Table('function_dependency', Base.metadata,
    Column('function_version_id', Integer, ForeignKey('function_versions.id')),
    Column('dependency_id', Integer, ForeignKey('functions.id'))
)

# **Define function_version_imports association table here**
function_version_imports = Table('function_version_imports', Base.metadata,
    Column('function_version_id', Integer, ForeignKey('function_versions.id')),
    Column('import_id', Integer, ForeignKey('imports.id'))
)


class Function(Base):
    __tablename__ = 'functions'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    versions = relationship("FunctionVersion", back_populates="function", cascade="all, delete-orphan")

class FunctionVersion(Base):
    __tablename__ = 'function_versions'
    id = Column(Integer, primary_key=True)
    function_id = Column(Integer, ForeignKey('functions.id'))
    version = Column(Integer)
    code = Column(String)
    function_metadata = Column(JSON)
    is_active = Column(Boolean, default=False)
    created_date = Column(DateTime, default=datetime.utcnow)
    input_parameters = Column(JSON)
    output_parameters = Column(JSON)
    function = relationship("Function", back_populates="versions")
    dependencies = relationship('Function', secondary=function_dependency,
                                primaryjoin=(function_dependency.c.function_version_id == id),
                                secondaryjoin=(function_dependency.c.dependency_id == Function.id))
    imports = relationship('Import', secondary=function_version_imports, back_populates='function_versions')
    triggers = Column(JSON, nullable=True)  # Store triggers as a JSON field



class Import(Base):
    __tablename__ = 'imports'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    lib = Column(String, nullable=True)
    source = Column(String)
    function_versions = relationship('FunctionVersion', secondary=function_version_imports, back_populates='imports')


class Log(Base):
    __tablename__ = 'logs'

    id = Column(Integer, primary_key=True)
    function_name = Column(String, nullable=False)
    message = Column(String, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    params = Column(JSON, nullable=True)
    output = Column(JSON, nullable=True)
    time_spent = Column(Float, nullable=True)
    log_type = Column(String, nullable=False)

    # Parent Log Relationship
    parent_log_id = Column(Integer, ForeignKey('logs.id'), nullable=True)
    parent_log = relationship(
        'Log',
        remote_side=[id],
        backref='child_logs',
        foreign_keys=[parent_log_id]
    )

    # Triggered By Log Relationship
    triggered_by_log_id = Column(Integer, ForeignKey('logs.id'), nullable=True)
    triggered_by_log = relationship(
        'Log',
        remote_side=[id],
        backref='triggered_logs',
        foreign_keys=[triggered_by_log_id]
    )


class SecretKey(Base):
    __tablename__ = 'secret_keys'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)  # Make name unique
    _encrypted_value = Column(LargeBinary, nullable=False)

    @hybrid_property
    def value(self):
        if self._encrypted_value:
            try:
                return fernet.decrypt(self._encrypted_value).decode()
            except InvalidToken:
                print(f"Error decrypting value for key: {self.name}. The encryption key may have changed.")
                return None
        return None

    @value.setter
    def value(self, plaintext_value):
        if plaintext_value:
            self._encrypted_value = fernet.encrypt(plaintext_value.encode())
        else:
            self._encrypted_value = None

