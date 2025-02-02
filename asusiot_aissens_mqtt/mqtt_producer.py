from typing import Any, Optional

import paho.mqtt.client as mqtt

from asusiot_aissens_mqtt.mqtt_config import MQTTConfig


class MQTTProducer:
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client = mqtt.Client(client_id=config.client_id)

        if config.username and config.password:
            self.client.username_pw_set(config.username, config.password)

        self.client.on_connect = self._on_connect

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: dict, rc: int
    ) -> None:
        if rc == 0:
            print(f"Connected to MQTT broker {self.config.broker} as Producer")
        else:
            print(f"Failed to connect to MQTT broker with code: {rc}")

    def connect(self) -> None:
        """Connect to MQTT broker"""
        self.client.connect(self.config.broker, self.config.port)

    def start(self) -> None:
        """Start the MQTT client loop"""
        self.client.loop_start()

    def stop(self) -> None:
        """Stop the MQTT client loop"""
        self.client.loop_stop()
        self.client.disconnect()

    def publish(
        self,
        topic: Optional[str] = None,
        payload: Any = None,
        qos: Optional[int] = None,
        retain: bool = False,
    ) -> None:
        """
        Publish a message to a topic.
        If topic is None, uses the default topic from configuration.
        If qos is None, uses the default qos from configuration.
        """
        topic_to_use = topic if topic is not None else self.config.topic
        qos_to_use = qos if qos is not None else self.config.qos
        self.client.publish(topic_to_use, payload, qos=qos_to_use, retain=retain)
