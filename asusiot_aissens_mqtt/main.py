import signal
import sys
from typing import Dict

import yaml

from asusiot_aissens_mqtt.mqtt_config import MQTTConfig
from asusiot_aissens_mqtt.mqtt_consumer import MQTTConsumer
from asusiot_aissens_mqtt.mqtt_producer import MQTTProducer


def main():
    config = load_config()
    mqtt_config = config["mqtt"]

    mqtt_producer_config = MQTTConfig(
        broker=mqtt_config["broker"],
        topic=mqtt_config["producer"]["topics"][0]["name"],
        qos=mqtt_config["producer"]["topics"][0]["qos"],
        client_id=mqtt_config["producer"]["client_id"],
    )
    mqtt_producer = MQTTProducer(mqtt_producer_config)

    mqtt_consumer_configs = [
        MQTTConfig(
            broker=mqtt_config["broker"],
            topic=topic["name"],
            qos=topic["qos"],
            client_id=f"{mqtt_config['consumer']['client_id']}_{i}",
        )
        for i, topic in enumerate(mqtt_config["consumer"]["topics"])
    ]
    mqtt_consumers = [MQTTConsumer(config) for config in mqtt_consumer_configs]
    for consumer in mqtt_consumers:
        consumer.set_message_callback(on_message)

    try:
        while True:
            # mqtt_producer.connect()
            # mqtt_producer.start()

            for consumer in mqtt_consumers:
                consumer.connect()
                consumer.start()

            signal.pause()
    finally:
        for consumer in mqtt_consumers:
            consumer.stop()
        if mqtt_producer:
            mqtt_producer.stop()


def load_config(config_path: str = "config.yaml") -> Dict:
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def on_message(topic: str, payload: bytes) -> None:
    print(f"Received message on topic {topic}: {payload}")


def signal_handler(sig, frame):
    print("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    main()
