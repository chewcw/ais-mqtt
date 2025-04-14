from typing import Optional

from pydantic import BaseModel


class MQTTConfig(BaseModel):
    broker: str
    port: int = 1883
    topic: str
    qos: int = 0
    username: Optional[str] = None
    password: Optional[str] = None
    client_id: str = "mqtt_client"
    plugin: str
