from datetime import datetime
from typing import Any, Dict

from pydantic.config import JsonValue

from asusiot_aissens_mqtt.plugins.interface import Plugin


class Stdout(Plugin):
    def input(self, topic: str, payload: bytes, userdata: Any) -> None:
        print(f"Received message on topic {topic}")
        print(f"Payload (hex): {payload.hex()}")  # Print hex representation instead
        data_str = payload.hex()
        data: Dict[str, JsonValue] = {"bytes": data_str}
        timestamp = datetime.now()
        name = topic.split("/")[0]  # Get the sensor name
        self._output(timestamp, name, data)

    def _output(self, timestamp: datetime, name: str, data: JsonValue) -> None:
        print(f"Timestamp: {timestamp}")
        print(f"Name: {name}")
        print(f"Data: {data}")
