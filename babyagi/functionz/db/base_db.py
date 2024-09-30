from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

class BaseDB(ABC):
    # Function management
    @abstractmethod
    def add_function(self, name: str, code: str, metadata: Optional[Dict[str, Any]] = None,
                     dependencies: Optional[List[str]] = None,
                     input_parameters: Optional[List[Dict[str, Any]]] = None,
                     output_parameters: Optional[List[Dict[str, Any]]] = None) -> None:
        pass

    @abstractmethod
    def get_function(self, name: str) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_all_functions(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_function(self, name: str, code: Optional[str] = None,
                        metadata: Optional[Dict[str, Any]] = None,
                        dependencies: Optional[List[str]] = None,
                        input_parameters: Optional[List[Dict[str, Any]]] = None,
                        output_parameters: Optional[List[Dict[str, Any]]] = None) -> None:
        pass

    @abstractmethod
    def remove_function(self, name: str) -> None:
        pass

    @abstractmethod
    def get_function_versions(self, name: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def activate_function_version(self, name: str, version: int) -> None:
        pass

    # Import management
    @abstractmethod
    def add_import(self, name: str, source: str, lib: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def get_all_imports(self) -> List[Dict[str, Any]]:
        pass

    # Logging
    @abstractmethod
    def add_log(self, function_name: str, message: str, timestamp: datetime,
                params: Optional[Dict[str, Any]] = None,
                output: Optional[Any] = None,
                time_spent: Optional[float] = None) -> None:
        pass

    @abstractmethod
    def get_logs(self, function_name: Optional[str] = None,
                 start_date: Optional[datetime] = None,
                 end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        pass