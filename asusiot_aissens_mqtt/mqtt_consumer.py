import paho.mqtt.client as mqtt
from typing import Optional, Callable, Any
import logging
from asusiot_aissens_mqtt.mqtt_config import MQTTConfig

logger = logging.getLogger(__name__)


class MQTTConsumer:
    def __init__(self, config: MQTTConfig):
        self.config = config
        self.client = mqtt.Client(client_id=config.client_id)
        self.message_callback: Optional[Callable[[str, bytes, Any], None]] = None

        if config.username and config.password:
            self.client.username_pw_set(config.username, config.password)

        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(
        self, client: mqtt.Client, userdata: Any, flags: dict, rc: int
    ) -> None:
        if rc == 0:
            logger.info(f"Connected to MQTT broker {self.config.broker}")
            logger.info(f"Subscribing to topic: {self.config.topic}")
            self.client.subscribe(self.config.topic, self.config.qos)
        else:
            logger.error(f"Failed to connect to MQTT broker with code: {rc}")

    def _on_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        if self.message_callback:
            self.message_callback(msg.topic, msg.payload, userdata)

    def set_message_callback(self, callback: Callable[[str, bytes, Any], None]) -> None:
        """Set callback function to handle incoming messages"""
        self.message_callback = callback

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
