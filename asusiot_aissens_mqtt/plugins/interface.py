from abc import ABC, abstractmethod
from typing import Any


class Plugin(ABC):
    @abstractmethod
    def input(self, topic: str, payload: bytes, userdata: Any) -> None:
        raise NotImplementedError("Plugin must implement input method")
