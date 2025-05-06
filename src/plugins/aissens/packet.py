import importlib
import logging
import os
from typing import Any

import yaml

from src.plugins.aissens.packet_processor import (
    BytesExtractInput,
    HexToNumberInput,
    PacketProcessor,
)
from src.plugins.aissens.packet_fft import PacketFFTDecoder
from src.plugins.aissens.packet_oa_only import (
    PacketOADecoder,
)
from src.plugins.interface import Plugin
from src.tools.tools_interface import OutputInterface

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

pp = PacketProcessor()


class Packet(Plugin):
    def __init__(self) -> None:
        config = self._load_config()
        self.output_name = config.get("output", {}).get("name", "data")
        tool_path = config.get("tool", "tools.sqlite.sqlite")
        self.data_saver = self._create_data_saver(tool_path)
        logger.info(f"Using output name: {self.output_name}")

    def _create_data_saver(self, tool_path: str) -> OutputInterface:
        """
        Create data saver instance based on tool configuration.

        Args:
            tool_path (str): Dot-separated path to tool module (e.g. "tools.stdout.stdout")

        Returns:
            OutputInterface: Configured data saver instance
        """
        try:
            # Import the module
            module_path = f"src.{tool_path}"
            module = importlib.import_module(module_path)

            # Get the class name from the last part of the path and capitalize it
            class_name = tool_path.split(".")[-1].capitalize()
            class_obj = getattr(module, class_name)

            # Validate it implements the OutputInterface
            if not issubclass(class_obj, OutputInterface):
                raise ValueError(
                    f"Class {class_obj.__name__} must implement OutputInterface"
                )

            # Create and return the instance
            return class_obj()

        except Exception as e:
            logger.error(f"Failed to create data saver: {str(e)}")
            logger.warning("Falling back to Sqlite")
            from src.tools.sqlite.sqlite import Sqlite

            return Sqlite()

    def _load_config(self) -> dict:
        """Load configuration from config/config.yaml or fallback to config/config_example.yaml"""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        config_dir = os.path.join(current_dir, "config")
        config_path = os.path.join(config_dir, "config.yaml")
        example_config_path = os.path.join(config_dir, "config_example.yaml")

        try:
            if os.path.exists(config_path):
                with open(config_path, "r") as f:
                    logger.info("Loaded configuration from config/config.yaml")
                    return yaml.safe_load(f)
            else:
                logger.warning(
                    "config/config.yaml not found, using config/config_example.yaml"
                )
                with open(example_config_path, "r") as f:
                    logger.info("Loaded configuration from config/config_example.yaml")
                    return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load config: {str(e)}")
            return {"output": {"name": "vibration_data"}}

    def input(self, topic: str, payload: bytes, userdata: Any) -> None:
        logger.debug(
            f"Received message on topic {topic}, payload: {payload.hex()[:10]}..."
        )

        try:
            # Extract the data type from the packet
            extract_input = BytesExtractInput(data=payload, offset=0, length=1)
            data_type_hex = pp.extract_hex(extract_input)
            number_input = HexToNumberInput(
                hex_str=data_type_hex, data_type="int", endian="little"
            )
            data_type = pp.hex_to_number(number_input)
            logger.debug(f"The received message data type: {data_type}")

            # FFT related packets (1: FFT data, 6: Real time FFT, 71/72: Raw data + FFT)
            if data_type in [1, 6, 71, 72]:
                logger.debug(f"Received FFT data packet on topic {topic}")
                try:
                    decoder = PacketFFTDecoder(payload)
                    decoder.decode()
                    sensor_name = self._get_sensor_name(topic)
                    if decoder.fft_packet:
                        self._output(
                            self.output_name,
                            {
                                "timestamp": decoder.fft_packet.timestamp.isoformat(),
                                "sensor_name": sensor_name,
                                "data_type": data_type,
                                "json_value": decoder.to_json(),
                            },
                        )
                    else:
                        raise Exception("")
                except Exception as e:
                    logger.error(f"Failed to decode FFT packet: {str(e)}")

            # OA related packets (9: OA only, 10: Real time OA only)
            elif data_type in [9, 10]:
                logger.debug(f"Received OA data packet on topic {topic}")
                try:
                    decoder = PacketOADecoder(payload)
                    decoder.decode()
                    sensor_name = self._get_sensor_name(topic)
                    if decoder.oa_packet:
                        self._output(
                            self.output_name,
                            {
                                "timestamp": decoder.oa_packet.timestamp.isoformat(),
                                "sensor_name": sensor_name,
                                "data_type": data_type,
                                "json_value": decoder.to_json(),
                            },
                        )
                    else:
                        raise Exception("")
                except Exception as e:
                    logger.error(f"Failed to decode OA packet: {str(e)}")

            # Handle not supported data types
            else:
                logger.warning(
                    f"Received unsupported data type {data_type} on topic {topic}"
                )

        except Exception as e:
            logger.error(f"Failed to process packet: {str(e)}")

    def _output(self, name: str, data: dict) -> None:
        # Save the data to the database
        try:
            # Log truncated data for debugging - safely convert dict to string for logging
            logger.debug(f"Writing data to {name}: {str(data)[:100]}{'...' if len(str(data)) > 100 else ''}")
            self.data_saver.output(name, **data)
        except Exception as e:
            logger.error(f"Failed to save data to the database: {str(e)}")

    def _get_sensor_name(self, topic: str) -> str:
        return topic.split("/")[0]
