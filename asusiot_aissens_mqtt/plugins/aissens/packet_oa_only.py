from dataclasses import dataclass
from datetime import datetime
from typing import cast

from asusiot_aissens_mqtt.packet_processor import (
    BytesExtractInput,
    HexToNumberInput,
    HexToTimestampInput,
    PacketProcessor,
)
from asusiot_aissens_mqtt.plugins.aissens.packet_common import (
    DATA_TYPE_MAP,
    DataTypeName,
)

pp = PacketProcessor()


@dataclass
class PacketOAOnly:
    """
    Data class representing an OA (Overall) packet with sensor data.

    This class contains all the fields necessary to store and process OA (Overall)
    data from a sensor, including basic sensor measurements and overall acceleration values
    across three axes.

    Attributes:
        data_type (int): Type of data packet (0-255, see type table in code)
        data_type_name (str): Human readable name for the data type (e.g. "Raw data", "OA only", etc.)
        data_length (int): Length of the data payload
        timestamp (datetime): Timestamp of when the data was captured
        status (byte): Status byte indicating sensor state
        battery_level (int): Current battery level
        adcavg (float): Average ADC value
        adclast (float): Last ADC value
        temperature (float): Temperature reading
        oa_x (float): Overall acceleration on X axis
        oa_y (float): Overall acceleration on Y axis
        oa_z (float): Overall acceleration on Z axis
        reserved (int): Reserved value for future use
    """

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
    data_type_name: DataTypeName
    data_length: int
    timestamp: datetime
    status: int
    battery_level: int
    adcavg: float
    adclast: float
    temperature: float
    oa_x: float
    oa_y: float
    oa_z: float
    reserved: str


class PacketOADecoder:
    """
    Decoder class for OA (Overall) packets.

    This class handles the decoding of binary OA packet data into structured data format.
    It processes the binary data and extracts all relevant fields including header information,
    sensor measurements, and overall acceleration values for all three axes.

    Attributes:
        file_bytes (bytes): Raw binary data to be decoded
        packet (PacketOAOnly): Decoded packet data
    """

    def __init__(self, file_bytes: bytes):
        """
        Initialize the FFT packet decoder.

        Args:
            file_bytes (bytes): Raw binary data to be decoded
        """
        self.file_bytes = file_bytes
        self.oa_packet: PacketOAOnly | None = None

    def decode(self) -> PacketOAOnly:
        """
        Decode the binary data into structured OA packet data.
        [...]
        """
        data_type_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=0, length=1)
        )
        data_type = int(
            pp.hex_to_number(
                HexToNumberInput(
                    hex_str=data_type_hex, data_type="int", endian="little"
                )
            )
        )
        # Ensure data_type_name is one of the valid literals from the PacketOAOnly type
        data_type_name = cast(DataTypeName, DATA_TYPE_MAP.get(data_type, "Reserved"))

        data_length_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=1, length=4)
        )
        data_length = int(
            pp.hex_to_number(
                HexToNumberInput(hex_str=data_length_hex, data_type="int", endian="big")
            )
        )

        timestamp_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=5, length=8)
        )
        timestamp = pp.hex_to_timestamp(
            HexToTimestampInput(hex_str=timestamp_hex, endian="little")
        )

        status_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=13, length=1)
        )
        status = int(
            pp.hex_to_number(
                HexToNumberInput(hex_str=status_hex, data_type="int", endian="little")
            )
        )

        battery_level_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=14, length=1)
        )
        battery_level = int(
            pp.hex_to_number(
                HexToNumberInput(
                    hex_str=battery_level_hex, data_type="int", endian="little"
                )
            )
        )

        adcavg_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=15, length=2)
        )
        adcavg = pp.hex_to_number(
            HexToNumberInput(hex_str=adcavg_hex, data_type="int", endian="little")
        )
        adcavg = adcavg / 1000

        adclast_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=17, length=2)
        )
        adclast = pp.hex_to_number(
            HexToNumberInput(hex_str=adclast_hex, data_type="int", endian="little")
        )
        adclast = adclast / 1000

        temperature_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=19, length=2)
        )
        temperature = pp.hex_to_number(
            HexToNumberInput(hex_str=temperature_hex, data_type="int", endian="little")
        )
        temperature = temperature / 1000

        oa_x_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=21, length=4)
        )
        oa_x = float(
            pp.hex_to_number(
                HexToNumberInput(hex_str=oa_x_hex, data_type="float", endian="little")
            )
        )

        oa_y_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=25, length=4)
        )
        oa_y = float(
            pp.hex_to_number(
                HexToNumberInput(hex_str=oa_y_hex, data_type="float", endian="little")
            )
        )

        oa_z_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=29, length=4)
        )
        oa_z = float(
            pp.hex_to_number(
                HexToNumberInput(hex_str=oa_z_hex, data_type="float", endian="little")
            )
        )

        reserved_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=33, length=17)
        )
        reserved = reserved_hex

        self.oa_packet = PacketOAOnly(
            data_type=data_type,
            data_type_name=data_type_name,
            data_length=data_length,
            timestamp=timestamp,
            status=status,
            battery_level=battery_level,
            adcavg=adcavg,
            adclast=adclast,
            temperature=temperature,
            oa_x=oa_x,
            oa_y=oa_y,
            oa_z=oa_z,
            reserved=reserved,
        )

        return self.oa_packet

    def to_json(self) -> dict:
        """
        Converts the OAPacket instance to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary containing all OAPacket data in a JSON-serializable format

        Raises:
            ValueError: If no packet data is available (packet not decoded yet)
        """
        if self.oa_packet is None:
            raise ValueError(
                "No packet data available. Please decode the packet first."
            )

        return {
            "data_type": self.oa_packet.data_type,
            "data_type_name": self.oa_packet.data_type_name,
            "data_length": self.oa_packet.data_length,
            "timestamp": self.oa_packet.timestamp.isoformat(),
            "status": self.oa_packet.status,
            "battery_level": self.oa_packet.battery_level,
            "adcavg": self.oa_packet.adcavg,
            "adclast": self.oa_packet.adclast,
            "temperature": self.oa_packet.temperature,
            "oa_x": float(self.oa_packet.oa_x),
            "oa_y": float(self.oa_packet.oa_y),
            "oa_z": float(self.oa_packet.oa_z),
            "reserved": self.oa_packet.reserved,
        }
