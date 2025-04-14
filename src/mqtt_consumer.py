import paho.mqtt.client as mqtt
from typing import Optional, Callable, Any
import logging
import time
from src.mqtt_config import MQTTConfig

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
        """Connect to MQTT broker with retry mechanism"""
        max_retries = 5
        retry_delay = 2  # seconds

        for attempt in range(1, max_retries + 1):
            try:
                logger.info(
                    f"Attempting to connect to {self.config.broker}:{self.config.port} (attempt {attempt}/{max_retries})"
                )
                self.client.connect(self.config.broker, self.config.port)
                logger.info(
                    f"Successfully connected to {self.config.broker}:{self.config.port}"
                )
                return
            except Exception as e:
                logger.error(
                    f"Connection attempt {attempt}/{max_retries} failed: {str(e)}"
                )
                if attempt < max_retries:
                    wait_time = retry_delay * (
                        2 ** (attempt - 1)
                    )  # Exponential backoff
                    logger.info(f"Waiting {wait_time} seconds before next attempt")
                    time.sleep(wait_time)
                else:
                    logger.error(f"Failed to connect after {max_retries} attempts")
                    raise

    def start(self) -> None:
        """Start the MQTT client loop"""
        self.client.loop_start()

    def stop(self) -> None:
        """Stop the MQTT client loop"""
        self.client.loop_stop()
        self.client.disconnect()
