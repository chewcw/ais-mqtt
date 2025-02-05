import importlib
import logging
import threading
from typing import Any, Dict, List

from asusiot_aissens_mqtt.mqtt_config import MQTTConfig
from asusiot_aissens_mqtt.mqtt_consumer import MQTTConsumer
from asusiot_aissens_mqtt.plugins.interface import Plugin

logger = logging.getLogger(__name__)


class MQTTConfigError(Exception):
    """Exception raised for errors in the MQTT configuration."""


class MQTT(threading.Thread):
    def __init__(self, config: Dict):
        super().__init__()
        self.config = config
        self.mqtt_consumers: List[MQTTConsumer] = []
        self._stop_event = threading.Event()
        self._validate_and_initialize_config(config)

    def _validate_and_initialize_config(self, config: Dict) -> None:
        """Validate configuration and initialize MQTT components."""
        try:
            if not isinstance(config, dict):
                raise MQTTConfigError("Configuration must be a dictionary")

            # Check for mqtt key first
            if "mqtt" not in config:
                raise MQTTConfigError("Missing 'mqtt' configuration")

            mqtt_config = config["mqtt"]

            # Validate mqtt configuration
            missing_fields = [
                field for field in ["broker", "consumer"] if field not in mqtt_config
            ]
            if missing_fields:
                raise MQTTConfigError(
                    f"Missing required fields in mqtt config: {', '.join(missing_fields)}"
                )

            # Initialize with mqtt_config instead of config
            self._initialize_consumers(mqtt_config)
        except (KeyError, TypeError, ValueError) as e:
            raise MQTTConfigError(f"Invalid configuration: {str(e)}")

    def _validate_base_config(self, config: Dict) -> None:
        """Validate base configuration structure."""
        if not isinstance(config, dict):
            raise MQTTConfigError("Configuration must be a dictionary")

        missing_fields = [
            field for field in ["broker", "consumer"] if field not in config
        ]
        if missing_fields:
            raise MQTTConfigError(
                f"Missing required fields: {', '.join(missing_fields)}"
            )

    def _validate_component_config(self, config: Dict, component: str) -> None:
        """Validate consumer configuration."""
        if not isinstance(config[component], dict):
            raise MQTTConfigError(
                f"{component.capitalize()} configuration must be a dictionary"
            )
        if "topics" not in config[component] or not config[component]["topics"]:
            raise MQTTConfigError(f"{component.capitalize()} topics not configured")
        if "client_id" not in config[component]:
            raise MQTTConfigError(f"{component.capitalize()} client_id not configured")

    def _initialize_consumers(self, mqtt_config: Dict) -> None:
        """Initialize MQTT consumers."""
        self._validate_component_config(mqtt_config, "consumer")
        mqtt_consumer_configs = [
            self._create_consumer_config(mqtt_config, topic, i)
            for i, topic in enumerate(mqtt_config["consumer"]["topics"])
        ]

        self.mqtt_consumers = [MQTTConsumer(config) for config in mqtt_consumer_configs]

        for consumer in self.mqtt_consumers:
            consumer.set_message_callback(self._on_message)

    def _create_consumer_config(
        self, mqtt_config: Dict, topic: Dict, index: int
    ) -> MQTTConfig:
        """Create configuration for a single consumer."""
        return MQTTConfig(
            broker=mqtt_config["broker"],
            port=mqtt_config.get("port", 1883),
            topic=topic.get("name", ""),
            qos=topic.get("qos", 0),
            plugin=topic.get("plugin", "default"),
            client_id=f"{mqtt_config['consumer']['client_id']}_{index}",
        )

    def load_plugin(self, name: str) -> Plugin:
        """Load a plugin module."""
        parts = name.split(".")
        module_path = f"asusiot_aissens_mqtt.plugins.{'.'.join(parts)}"
        module = importlib.import_module(module_path)
        class_name = parts[-1].capitalize()
        return getattr(module, class_name)()

    def _on_message(self, topic: str, payload: bytes, userdata: Any) -> None:
        """Handle incoming MQTT messages."""
        topics = self.config.get("mqtt", {}).get("consumer", {}).get("topics", [])
        # Find the matching topic configuration
        topic_conf = next((item for item in topics if item.get("name") == topic), None)
        if topic_conf:
            plugin_name = topic_conf.get("plugin")
            if plugin_name:
                plugin_instance = self.load_plugin(plugin_name)
                plugin_instance.input(topic, payload, userdata)
                logger.info(f"Plugin {plugin_name} called for topic: {topic}")
            else:
                logger.info(f"No plugin configured for topic: {topic}")
        else:
            logger.info(f"No configuration found for topic: {topic}")

    def run(self) -> None:
        """Run the MQTT thread."""
        try:
            for consumer in self.mqtt_consumers:
                consumer.connect()
                consumer.start()

            self._stop_event.wait()

        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up MQTT connections."""
        for consumer in self.mqtt_consumers:
            consumer.stop()

    def stop(self) -> None:
        """Signal the thread to stop."""
        self._stop_event.set()

    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
        self.join()
