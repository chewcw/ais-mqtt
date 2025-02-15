import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from pydantic.config import JsonValue

from asusiot_aissens_mqtt.plugins.output.output_interface import OutputInterface
from asusiot_aissens_mqtt.plugins.output.db.sqlite import SqliteDataSaver
from asusiot_aissens_mqtt.packet_processor import (
    BytesExtractInput,
    HexToNumberInput,
    PacketProcessor,
)
from asusiot_aissens_mqtt.plugins.input.aissens.packet_fft import PacketFFTDecoder
from asusiot_aissens_mqtt.plugins.input.aissens.packet_oa_only import (
    PacketOADecoder,
)
from asusiot_aissens_mqtt.plugins.input.interface import Plugin

logger = logging.getLogger(__name__)

pp = PacketProcessor()


class Packet(Plugin):
    def __init__(self) -> None:
        # Read config file
        config_path = Path(__file__).parent / "config.yaml"
        with open(config_path, "r") as file:
            config = yaml.safe_load(file)

        db_path = config.get("database", {}).get("path", "sensor_data.db")
        self.data_saver: OutputInterface = SqliteDataSaver(db_path)

    def input(self, topic: str, payload: bytes, userdata: Any) -> None:
        logger.debug(
            f"Received message on topic {topic}, payload: {payload.hex()[:20]}..."
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
                            decoder.fft_packet.timestamp,
                            sensor_name,
                            decoder.to_json(),
                        )
                    else:
                        raise Exception("")
                except Exception as e:
                    logger.error(f"Failed to decode FFT packet: {str(e)}")

            # OA related packets (9: OA only, 10: Real time OA only)
            if data_type in [9, 10]:
                logger.debug(f"Received OA data packet on topic {topic}")
                try:
                    decoder = PacketOADecoder(payload)
                    decoder.decode()
                    sensor_name = self._get_sensor_name(topic)
                    if decoder.oa_packet:
                        self._output(
                            decoder.oa_packet.timestamp,
                            sensor_name,
                            decoder.to_json(),
                        )
                    else:
                        raise Exception("")
                except Exception as e:
                    logger.error(f"Failed to decode OA packet: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to process packet: {str(e)}")

    def _output(self, timestamp: datetime, name: str, data: JsonValue) -> None:
        # Save the data to the database
        try:
            self.data_saver.output(timestamp, name, data)
        except Exception as e:
            logger.error(f"Failed to save data to the database: {str(e)}")

    def _get_sensor_name(self, topic: str) -> str:
        return topic.split("/")[0]
