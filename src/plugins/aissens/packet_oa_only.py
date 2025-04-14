import json
from dataclasses import dataclass
from datetime import datetime
from typing import cast


from src.plugins.aissens.packet_processor import (
    BytesExtractInput,
    HexToNumberInput,
    HexToTimestampInput,
    PacketProcessor,
)
from src.plugins.aissens.packet_common import (
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


class OADecodeError(Exception):
    def __init__(self, field_name: str, original_error: Exception):
        self.field_name = field_name
        self.original_error = original_error
        super().__init__(f"Error decoding field '{field_name}': {str(original_error)}")


class PacketOADecoder:
    def __init__(self, file_bytes: bytes):
        self.file_bytes = file_bytes
        self.oa_packet: PacketOAOnly | None = None

    def decode(self) -> PacketOAOnly:
        """
        Decode the binary data into structured OA packet data.
        Raises OADecodeError with specific field information on failure.
        """
        try:
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
        except Exception as e:
            raise OADecodeError("data_type", e)

        try:
            data_type_name = cast(
                DataTypeName, DATA_TYPE_MAP.get(data_type, "Reserved")
            )
        except Exception as e:
            raise OADecodeError("data_type_name", e)

        try:
            data_length_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=1, length=4)
            )
            data_length = int(
                pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=data_length_hex, data_type="int", endian="big"
                    )
                )
            )
        except Exception as e:
            raise OADecodeError("data_length", e)

        try:
            timestamp_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=5, length=8)
            )
            timestamp = pp.hex_to_timestamp(
                HexToTimestampInput(hex_str=timestamp_hex, endian="little")
            )
        except Exception as e:
            raise OADecodeError("timestamp", e)

        try:
            status_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=13, length=1)
            )
            status = int(
                pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=status_hex, data_type="int", endian="little"
                    )
                )
            )
        except Exception as e:
            raise OADecodeError("status", e)

        try:
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
        except Exception as e:
            raise OADecodeError("battery_level", e)

        try:
            adcavg_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=15, length=2)
            )
            adcavg = pp.hex_to_number(
                HexToNumberInput(hex_str=adcavg_hex, data_type="int", endian="little")
            )
            adcavg = adcavg / 1000
        except Exception as e:
            raise OADecodeError("adcavg", e)

        try:
            adclast_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=17, length=2)
            )
            adclast = pp.hex_to_number(
                HexToNumberInput(hex_str=adclast_hex, data_type="int", endian="little")
            )
            adclast = adclast / 1000
        except Exception as e:
            raise OADecodeError("adclast", e)

        try:
            temperature_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=19, length=2)
            )
            temperature = pp.hex_to_number(
                HexToNumberInput(
                    hex_str=temperature_hex, data_type="int", endian="little"
                )
            )
            temperature = temperature / 1000
        except Exception as e:
            raise OADecodeError("temperature", e)

        try:
            oa_x_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=21, length=4)
            )
            oa_x = float(
                pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=oa_x_hex, data_type="float", endian="little"
                    )
                )
            )
        except Exception as e:
            raise OADecodeError("oa_x", e)

        try:
            oa_y_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=25, length=4)
            )
            oa_y = float(
                pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=oa_y_hex, data_type="float", endian="little"
                    )
                )
            )
        except Exception as e:
            raise OADecodeError("oa_y", e)

        try:
            oa_z_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=29, length=4)
            )
            oa_z = float(
                pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=oa_z_hex, data_type="float", endian="little"
                    )
                )
            )
        except Exception as e:
            raise OADecodeError("oa_z", e)

        try:
            reserved_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=33, length=17)
            )
            reserved = reserved_hex
        except Exception as e:
            raise OADecodeError("reserved", e)

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

    def to_json(self) -> str:
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

        return json.dumps({
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
        })
