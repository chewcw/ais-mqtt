from abc import ABC, abstractmethod
from datetime import datetime

from pydantic.config import JsonValue


class OutputInterface(ABC):
    @abstractmethod
    def output(self, timestamp: datetime, name: str, json_value: JsonValue) -> None:
        """
        Output data to target.

        Args:
            timestamp (datetime): The timestamp for the record.
            name (str): The name or type of data.
            json_value (JsonValue): The JSON value to be saved.
        """
        pass
