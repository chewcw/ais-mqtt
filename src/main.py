import logging
import os
import signal
import sys
from typing import Dict

import yaml

from src.mqtt import MQTT
# from src.plugins.aissens.packet_test import main as packet_test_main

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


def load_config(config_path: str = "config/config.yaml") -> Dict:
    try:
        # Try to open the config file
        with open(config_path, "r") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        # If not found in the specified path, try to find it in alternative locations
        alt_paths = [
            "src/config/config.yaml",              # Root directory
            "/app/src/config/config.yaml",         # Docker mounted volume path
            os.path.join(os.path.dirname(os.path.dirname(__file__)), "config", "config.yaml")  # Relative to module
        ]
        
        for path in alt_paths:
            try:
                with open(path, "r") as file:
                    logger.info(f"Config loaded from alternative path: {path}")
                    return yaml.safe_load(file)
            except FileNotFoundError:
                continue
                
        logger.error(f"Config file {config_path} not found, and no alternatives available.")
        sys.exit(1)


def signal_handler(sig, frame):
    logger.info("Exiting...")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    main()
    # packet_test_main()
