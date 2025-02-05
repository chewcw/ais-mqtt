from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic.config import JsonValue


class Plugin(ABC):
    @abstractmethod
    def input(self, topic: str, payload: bytes, userdata: Any) -> None:
        raise NotImplementedError("Plugin must implement input method")

    @abstractmethod
    def _output(self, timestamp: datetime, name: str, data: JsonValue) -> None:
        raise NotImplementedError("Plugin must implement output method")
