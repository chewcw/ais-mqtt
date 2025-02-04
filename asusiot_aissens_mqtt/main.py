import logging
import signal
import sys
from typing import Dict

import yaml

from asusiot_aissens_mqtt.mqtt import MQTT

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


def main():
    config = load_config()
    with MQTT(config) as mqtt:
        try:
            mqtt.join()
        except KeyboardInterrupt:
            logger.info("Service interrupted by user")


def load_config(config_path: str = "config.yaml") -> Dict:
    with open(config_path, "r") as file:
        return yaml.safe_load(file)


def signal_handler(sig, frame):
    logger.info("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    main()
