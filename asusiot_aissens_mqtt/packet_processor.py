import struct
from typing import Literal, Union

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
        [Previous hex_to_number implementation remains the same]
        """
        hex_str = input_data.hex_str
        if len(hex_str) < 8:
            hex_str = hex_str.ljust(8, "0")
        elif len(hex_str) > 8:
            hex_str = hex_str[:8]

        byte_data = bytes.fromhex(hex_str)
        fmt = "<" if input_data.endian == "little" else ">"
        fmt += "f" if input_data.data_type == "float" else "i"

        return struct.unpack(fmt, byte_data)[0]
