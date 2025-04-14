import struct
from datetime import datetime
from typing import Literal, Union
from zoneinfo import ZoneInfo

from pydantic import BaseModel, field_validator


class BytesInput(BaseModel):
    data: bytes


class BytesExtractInput(BaseModel):
    data: bytes
    offset: int
    length: int


class HexToNumberInput(BaseModel):
    hex_str: str
    data_type: Literal["float", "int"] = "float"
    endian: Literal["big", "little"] = "little"

    @field_validator("data_type")
    def validate_data_type(cls, v):
        if v not in ["float", "int"]:
            raise ValueError('data_type must be either "float" or "int"')
        return v

    @field_validator("endian")
    def validate_endian(cls, v):
        if v not in ["big", "little"]:
            raise ValueError('endian must be either "big" or "little"')
        return v


class HexToTimestampInput(BaseModel):
    hex_str: str
    endian: Literal["big", "little"] = "little"

    @field_validator("endian")
    def validate_endian(cls, v):
        if v not in ["big", "little"]:
            raise ValueError('endian must be either "big" or "little"')
        return v


class PacketProcessor:
    def __init__(self):
        pass

    def print_hex(self, input_data: BytesInput) -> None:
        """
        Prints bytes content in hexadecimal format.

        Args:
            input_data (BytesInput): Pydantic model containing:
                - data (bytes): Bytes to be printed.

        Example:
            >>> processor = PacketProcessor()
            >>> processor.print_hex(BytesInput(data=b'\x01\x02\x03'))
            010203
        """
        hex_content = input_data.data.hex()
        print(hex_content)

    def extract_hex(self, input_data: BytesExtractInput) -> str:
        """
        Extracts a portion of bytes based on offset and length.

        Args:
            input_data (BytesExtractInput): Pydantic model containing:
                - data (bytes): Source bytes to extract from.
                - offset (int): Starting position in bytes (zero-based).
                - length (int): Number of bytes to extract.

        Returns:
            str: Hexadecimal representation of the extracted bytes.

        Example:
            >>> processor = PacketProcessor()
            >>> processor.extract_hex(BytesExtractInput(data=b'\x01\x02\x03\x04', offset=1, length=2))
            '0203'
        """
        content = input_data.data[
            input_data.offset : input_data.offset + input_data.length
        ]
        return content.hex()

    def hex_to_number(self, input_data: HexToNumberInput) -> Union[float, int]:
        """
        Converts hexadecimal string to a number (float or int).

        Args:
            input_data (HexToNumberInput): Pydantic model containing:
                - hex_str (str): Hexadecimal string (1 to 8 bytes)
                - data_type (str): Type of number to convert to ('float' or 'int')
                - endian (str): Byte order ('big' or 'little')

        Returns:
            Union[float, int]: Converted number based on data_type

        Example:
            >>> processor = PacketProcessor()
            >>> processor.hex_to_number(HexToNumberInput(hex_str='41200000', data_type='float'))
            10.0
        """
        hex_str = input_data.hex_str
        byte_data = bytes.fromhex(hex_str)
        byte_length = len(byte_data)

        # Define format string based on endianness
        fmt = "<" if input_data.endian == "little" else ">"

        # Add format specifier based on data type and byte length
        if input_data.data_type == "float":
            fmt += "f"  # single precision float (4 bytes)
            if byte_length != 4:
                raise ValueError(
                    "Float conversion requires exactly 4 bytes (8 hex characters)"
                )
        else:  # int
            if byte_length == 1:
                fmt += "b"  # signed char (1 byte)
            elif byte_length == 2:
                fmt += "h"  # short (2 bytes)
            elif byte_length <= 4:
                fmt += "i"  # int (4 bytes)
            else:
                fmt += "q"  # long long (8 bytes)

        # Unpack the bytes according to the format
        value = struct.unpack(fmt, byte_data)[0]

        return int(value) if input_data.data_type == "int" else value

    def hex_to_timestamp(self, input_data: HexToTimestampInput) -> datetime:
        """
        Converts 8 bytes hex string to UTC timestamp.

        Args:
            input_data (HexToTimestampInput): Pydantic model containing:
                - hex_str (str): Hexadecimal string (8 bytes/16 characters)
                - endian (str): Byte order ('big' or 'little')

        Returns:
            datetime: UTC Timestamp converted from hex bytes

        Example:
            >>> processor = PacketProcessor()
            >>> processor.hex_to_timestamp(HexToTimestampInput(hex_str='60851A1A00000000'))
            datetime.datetime(2021, 4, 25, 10, 26, 26)
        """
        hex_str = input_data.hex_str
        if len(hex_str) != 16:
            raise ValueError("Hex string must be exactly 8 bytes (16 characters)")

        byte_data = bytes.fromhex(hex_str)
        fmt = "<" if input_data.endian == "little" else ">"
        fmt += "Q"  # unsigned long long (8 bytes)

        timestamp = struct.unpack(fmt, byte_data)[0]
        # Get the system's local timezone and offset
        local_dt = datetime.now().astimezone()
        local_tz = local_dt.tzinfo
        if local_tz is not None:
            offset = local_tz.utcoffset(local_dt)
            if offset is not None:
                offset_seconds = offset.total_seconds()
                # Adjust the timestamp by subtracting the offset
                corrected_timestamp = timestamp - offset_seconds
                return datetime.fromtimestamp(corrected_timestamp, tz=local_tz)
            else:
                return datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
        else:
            return datetime.fromtimestamp(timestamp, tz=ZoneInfo("UTC"))
