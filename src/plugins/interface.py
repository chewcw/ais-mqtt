from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class Plugin(ABC):
    @abstractmethod
    def input(self, topic: str, payload: bytes, userdata: Any) -> None:
        raise NotImplementedError("Plugin must implement input method")

    @abstractmethod
    def _output(self, name: str, data: dict) -> None:
        raise NotImplementedError("Plugin must implement output method")
