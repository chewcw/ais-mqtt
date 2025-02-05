from abc import ABC, abstractmethod
from datetime import datetime

from pydantic.config import JsonValue


class DataSaverInterface(ABC):
    @abstractmethod
    def save(self, timestamp: datetime, name: str, json_value: JsonValue) -> None:
        """
        Save a data record into the database.

        Args:
            timestamp (datetime): The timestamp for the record.
            name (str): The name or type of data.
            json_value (JsonValue): The JSON value to be saved.
        """
        pass
