from datetime import datetime
from typing import Any, Dict

from pydantic.config import JsonValue

from asusiot_aissens_mqtt.plugins.output.output_interface import OutputInterface


class Stdout(OutputInterface):
    def input(self, topic: str, payload: bytes, userdata: Any) -> None:
        print(f"Received message on topic {topic}")
        print(f"Payload (hex): {payload.hex()}")  # Print hex representation instead
        data_str = payload.hex()
        data: Dict[str, JsonValue] = {"bytes": data_str}
        timestamp = datetime.now()
        name = topic.split("/")[0]  # Get the sensor name
        self.output(timestamp, name, data)

    def output(self, timestamp: datetime, name: str, json_value: JsonValue) -> None:
        print(f"Timestamp: {timestamp}")
        print(f"Name: {name}")
        print(f"Data: {json_value}")
