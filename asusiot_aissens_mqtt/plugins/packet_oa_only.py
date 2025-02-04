from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from numpy import byte

from asusiot_aissens_mqtt.packet_processor import (
    BytesExtractInput,
    HexToNumberInput,
    PacketProcessor,
)
from asusiot_aissens_mqtt.plugins.interface import Plugin
from asusiot_aissens_mqtt.plugins.packet_common import DATA_TYPE_MAP

pp = PacketProcessor()


@dataclass
class PacketOAOnly:
    """Packet OA Only."""

    # Data type
    # | Number (base10) | Data type               |
    # |-----------------|-------------------------|
    # | 0               | Raw data                |
    # | 1               | FFT data                |
    # | 2               | Feature                 |
    # | 3               | Battery                 |
    # | 4               | Hibernate               |
    # | 5               | Real time raw data      |
    # | 6               | Real time FFT           |
    # | 71, 72          | Raw data + FFT          |
    # | 81, 82          | Raw time raw data + FFT |
    # | 9               | OA only                 |
    # | 10              | Real time OA only       |
    # | 11              | Ask command             |
    # | 12 ~ 255        | Reserved                |

    data_type: int
    data_type_name: Literal[
        "Raw data",
        "FFT data",
        "Feature",
        "Battery",
        "Hibernate",
        "Real time raw data",
        "Real time FFT",
        "Raw data + FFT",
        "Raw time raw data + FFT",
        "OA only",
        "Real time OA only",
        "Ask command",
        "Reserved",
    ]
    data_length: int
    timestamp: datetime
    status: byte
    battery_level: int
    adcavg: int
    adclast: int
    temperature: int
    oa_x: float
    oa_y: float
    oa_z: float
    reserved: int


class OAPacketDecoder(Plugin):
    """
    Decoder class for OA Only packets.

    This class handles the decoding of OA Only packets.

    Attributes:
        file_bytes (bytes): Raw binary data to be decoded
    """

    def __init__(self, file_bytes: bytes):
        """
        Initialize the FFT packet decoder.

        Args:
            file_bytes (bytes): Raw binary data to be decoded
        """
        self.file_bytes = file_bytes

    def decode(self):
        data_type_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=0, length=1)
        )
        self.data_type = pp.hex_to_number(
            HexToNumberInput(hex_str=data_type_hex, data_type="int", endian="little")
        )
        self.data_type_naem = DATA_TYPE_MAP.get(int(self.data_type), "Reserved")

        data_length_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=1, length=4)
        )
        self.data_length = pp.hex_to_number(
            HexToNumberInput(hex_str=data_length_hex, data_type="int", endian="big")
        )

        timestamp_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=5, length=8)
        )
        timestamp = pp.hex_to_number(
            HexToNumberInput(hex_str=timestamp_hex, data_type="int", endian="little")
        )
        self.timestamp = datetime.fromtimestamp(timestamp)

        status_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=13, length=1)
        )
        status = pp.hex_to_number(
            HexToNumberInput(hex_str=status_hex, data_type="int", endian="little")
        )
        self.status = status

        battery_level_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=14, length=1)
        )
        battery_level = pp.hex_to_number(
            HexToNumberInput(
                hex_str=battery_level_hex, data_type="int", endian="little"
            )
        )
        self.battery_level = battery_level

        adcavg_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=15, length=2)
        )
        adcavg = pp.hex_to_number(
            HexToNumberInput(hex_str=adcavg_hex, data_type="int", endian="little")
        )
        self.adcavg = adcavg

        adclast_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=17, length=2)
        )
        adclast = pp.hex_to_number(
            HexToNumberInput(hex_str=adclast_hex, data_type="int", endian="little")
        )
        self.adclast = adclast

        temperature_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=19, length=2)
        )
        temperature = pp.hex_to_number(
            HexToNumberInput(hex_str=temperature_hex, data_type="int", endian="little")
        )
        self.temperature = temperature

        oa_x_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=21, length=4)
        )
        oa_x = pp.hex_to_number(
            HexToNumberInput(hex_str=oa_x_hex, data_type="float", endian="little")
        )
        self.oa_x = oa_x

        oa_y_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=25, length=4)
        )
        oa_y = pp.hex_to_number(
            HexToNumberInput(hex_str=oa_y_hex, data_type="float", endian="little")
        )
        self.oa_y = oa_y

        oa_z_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=29, length=4)
        )
        oa_z = pp.hex_to_number(
            HexToNumberInput(hex_str=oa_z_hex, data_type="float", endian="little")
        )
        self.oa_z = oa_z

        reserved_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=33, length=17)
        )
        reserved = pp.hex_to_number(
            HexToNumberInput(hex_str=reserved_hex, data_type="int", endian="little")
        )
        self.reserved = reserved
