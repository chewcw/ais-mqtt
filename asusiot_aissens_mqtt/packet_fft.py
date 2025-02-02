from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np

from asusiot_aissens_mqtt.packet_processor import (
    BytesExtractInput,
    HexToNumberInput,
    PacketProcessor,
)

pp = PacketProcessor()

DATA_TYPE_MAP = {
    0: "Raw data",
    1: "FFT data",
    2: "Feature",
    3: "Battery",
    4: "Hibernate",
    5: "Real time raw data",
    6: "Real time FFT",
    71: "Raw data + FFT",
    72: "Raw data + FFT",
    81: "Raw time raw data + FFT",
    82: "Raw time raw data + FFT",
    9: "OA only",
    10: "Real time OA only",
    11: "Ask command",
}


@dataclass
class FFTPacket:
    """
    Data class representing an FFT packet with sensor data.

    This class contains all the fields necessary to store and process FFT (Fast Fourier Transform)
    data from a sensor, including acceleration and velocity measurements across three axes.

    Attributes:
        data_type (int): Type of data packet (0-255, see type table in code)
        data_type_name (str): Human readable name for the data type (e.g. "Raw data", "FFT data", etc.)
        data_length (int): Length of the data payload
        timestamp (datetime): Timestamp of when the data was captured
        fft_result (int): Result of FFT calculation
        battery_level (int): Current battery level
        adcavg (int): Average ADC value
        adclast (int): Last ADC value
        temperature (int): Temperature reading
        oa_x (float): Overall acceleration on X axis
        oa_y (float): Overall acceleration on Y axis
        oa_z (float): Overall acceleration on Z axis
        freq_resolution (float): Frequency resolution of FFT
        fft_length (int): Length of FFT data
        report_len (int): Length of the report
        reserved_bytes (bytes): Reserved bytes for future use
        _acc_x_values (np.ndarray): Acceleration values for X axis
        _acc_y_values (np.ndarray): Acceleration values for Y axis
        _acc_z_values (np.ndarray): Acceleration values for Z axis
        _vec_x_values (np.ndarray): Velocity values for X axis
        _vec_y_values (np.ndarray): Velocity values for Y axis
        _vec_z_values (np.ndarray): Velocity values for Z axis
        velocity_data (dict): Dictionary containing velocity data for all axes
        acceleration_data (dict): Dictionary containing acceleration data for all axes
        acc_x_padded (np.ndarray): Zero-padded acceleration values for X axis
        acc_y_padded (np.ndarray): Zero-padded acceleration values for Y axis
        acc_z_padded (np.ndarray): Zero-padded acceleration values for Z axis
        vec_x_padded (np.ndarray): Zero-padded velocity values for X axis
        vec_y_padded (np.ndarray): Zero-padded velocity values for Y axis
        vec_z_padded (np.ndarray): Zero-padded velocity values for Z axis
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
    fft_result: int
    battery_level: int
    adcavg: int
    adclast: int
    temperature: int
    oa_x: float
    oa_y: float
    oa_z: float
    freq_resolution: float
    fft_length: int
    report_len: int
    reserved_bytes: bytes
    _acc_x_values: np.ndarray
    _acc_y_values: np.ndarray
    _acc_z_values: np.ndarray
    _vec_x_values: np.ndarray
    _vec_y_values: np.ndarray
    _vec_z_values: np.ndarray
    acc_x_padded: np.ndarray
    acc_y_padded: np.ndarray
    acc_z_padded: np.ndarray
    vec_x_padded: np.ndarray
    vec_y_padded: np.ndarray
    vec_z_padded: np.ndarray
    velocity_data: dict[str, np.ndarray]
    acceleration_data: dict[str, np.ndarray]


class FFTPacketDecoder:
    """
    Decoder class for FFT packets.

    This class handles the decoding of binary FFT packet data into structured data format.

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
        """
        Decode the binary data into structured FFT packet data.

        This method processes the binary data and extracts all relevant fields including:
        - Header information (data type, length, timestamp)
        - Sensor measurements (FFT result, battery level, ADC values, temperature)
        - Acceleration and velocity data for all three axes

        The method follows a specific byte order and data format defined by the protocol.
        """
        data_type_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=30, length=1)
        )
        self.data_type = pp.hex_to_number(
            HexToNumberInput(hex_str=data_type_hex, data_type="int", endian="little")
        )
        self.data_type_name = DATA_TYPE_MAP.get(int(self.data_type), "Reserved")

        data_length_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=31, length=4)
        )
        self.data_length = pp.hex_to_number(
            HexToNumberInput(hex_str=data_length_hex, data_type="int", endian="big")
        )

        timestamp_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=35, length=8)
        )
        timestamp = pp.hex_to_number(
            HexToNumberInput(hex_str=timestamp_hex, data_type="int", endian="little")
        )
        self.timestamp = datetime.fromtimestamp(timestamp)

        fft_result_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=43, length=1)
        )
        self.fft_result = pp.hex_to_number(
            HexToNumberInput(hex_str=fft_result_hex, data_type="int", endian="little")
        )

        battery_level_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=44, length=1)
        )
        self.battery_level = pp.hex_to_number(
            HexToNumberInput(
                hex_str=battery_level_hex, data_type="int", endian="little"
            )
        )

        adcavg_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=45, length=2)
        )
        self.adcavg = pp.hex_to_number(
            HexToNumberInput(hex_str=adcavg_hex, data_type="int", endian="little")
        )

        adclast_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=47, length=2)
        )
        self.adclast = pp.hex_to_number(
            HexToNumberInput(hex_str=adclast_hex, data_type="int", endian="little")
        )

        temperature_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=49, length=2)
        )
        self.temperature = pp.hex_to_number(
            HexToNumberInput(hex_str=temperature_hex, data_type="int", endian="little")
        )

        oa_x_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=51, length=4)
        )
        self.oa_x = pp.hex_to_number(
            HexToNumberInput(hex_str=oa_x_hex, data_type="float", endian="little")
        )

        oa_y_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=55, length=4)
        )
        self.oa_y = pp.hex_to_number(
            HexToNumberInput(hex_str=oa_y_hex, data_type="float", endian="little")
        )

        oa_z_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=59, length=4)
        )
        self.oa_z = pp.hex_to_number(
            HexToNumberInput(hex_str=oa_z_hex, data_type="float", endian="little")
        )

        freq_resolution_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=63, length=4)
        )
        self.freq_resolution = pp.hex_to_number(
            HexToNumberInput(
                hex_str=freq_resolution_hex, data_type="float", endian="little"
            )
        )

        fft_length_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=67, length=4)
        )
        self.fft_length = pp.hex_to_number(
            HexToNumberInput(hex_str=fft_length_hex, data_type="int", endian="big")
        )

        report_len_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=71, length=4)
        )
        self.report_len = pp.hex_to_number(
            HexToNumberInput(hex_str=report_len_hex, data_type="int", endian="big")
        )

        self.reserved_bytes_hex = pp.extract_hex(
            BytesExtractInput(data=self.file_bytes, offset=75, length=5)
        )
        self.reserved_bytes = bytes.fromhex(self.reserved_bytes_hex)

        acc_x_values = np.zeros(int(self.report_len))
        for i in range(int(self.report_len)):
            offset = 80 + i * 4
            acc_x_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
            )
            acc_x_value = pp.hex_to_number(
                HexToNumberInput(hex_str=acc_x_hex, data_type="float", endian="little")
            )
            acc_x_values[i] = acc_x_value

        acc_y_values = np.zeros(int(self.report_len))
        for i in range(int(self.report_len)):
            offset = int(80 + self.report_len * 4 + i * 4)
            acc_y_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
            )
            acc_y_value = pp.hex_to_number(
                HexToNumberInput(hex_str=acc_y_hex, data_type="float", endian="little")
            )
            acc_y_values[i] = acc_y_value

        acc_z_values = np.zeros(int(self.report_len))
        for i in range(int(self.report_len)):
            offset = int(80 + 2 * self.report_len * 4 + i * 4)
            acc_z_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
            )
            acc_z_value = pp.hex_to_number(
                HexToNumberInput(hex_str=acc_z_hex, data_type="float", endian="little")
            )
            acc_z_values[i] = acc_z_value
        self.acceleration_data = {
            "x": acc_x_values,
            "y": acc_y_values,
            "z": acc_z_values,
        }

        vec_x_values = np.zeros(int(self.report_len))
        for i in range(int(self.report_len)):
            offset = int(80 + 3 * self.report_len * 4 + i * 4)
            vec_x_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
            )
            vec_x_value = pp.hex_to_number(
                HexToNumberInput(hex_str=vec_x_hex, data_type="float", endian="little")
            )
            vec_x_values[i] = vec_x_value

        vec_y_values = np.zeros(int(self.report_len))
        for i in range(int(self.report_len)):
            offset = int(80 + 4 * self.report_len * 4 + i * 4)
            vec_y_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
            )
            vec_y_value = pp.hex_to_number(
                HexToNumberInput(hex_str=vec_y_hex, data_type="float", endian="little")
            )
            vec_y_values[i] = vec_y_value

        vec_z_values = np.zeros(int(self.report_len))
        for i in range(int(self.report_len)):
            offset = int(80 + 5 * self.report_len * 4 + i * 4)
            vec_z_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
            )
            vec_z_value = pp.hex_to_number(
                HexToNumberInput(hex_str=vec_z_hex, data_type="float", endian="little")
            )
            vec_z_values[i] = vec_z_value

        self.velocity_data = {"x": vec_x_values, "y": vec_y_values, "z": vec_z_values}

        # Create zero-padded arrays for FFT
        self.acc_x_padded = np.pad(
            self.acceleration_data["x"],
            [(0, int(self.fft_length - len(self.acceleration_data["x"])))],
            mode="constant",
        )
        self.acc_y_padded = np.pad(
            self.acceleration_data["y"],
            [(0, int(self.fft_length - len(self.acceleration_data["y"])))],
            mode="constant",
        )
        self.acc_z_padded = np.pad(
            self.acceleration_data["z"],
            [(0, int(self.fft_length - len(self.acceleration_data["z"])))],
            mode="constant",
        )

        self.vec_x_padded = np.pad(
            self.velocity_data["x"],
            [(0, int(self.fft_length - len(self.velocity_data["x"])))],
            mode="constant",
        )
        self.vec_y_padded = np.pad(
            self.velocity_data["y"],
            [(0, int(self.fft_length - len(self.velocity_data["y"])))],
            mode="constant",
        )
        self.vec_z_padded = np.pad(
            self.velocity_data["z"],
            [(0, int(self.fft_length - len(self.velocity_data["z"])))],
            mode="constant",
        )

    def to_json(self) -> dict:
        """
        Converts the FFTPacket instance to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary containing all FFTPacket data in a JSON-serializable format
        """
        return {
            "data_type": self.data_type,
            "data_type_name": self.data_type_name,
            "data_length": self.data_length,
            "timestamp": self.timestamp.isoformat(),
            "fft_result": self.fft_result,
            "battery_level": self.battery_level,
            "adcavg": self.adcavg,
            "adclast": self.adclast,
            "temperature": self.temperature,
            "oa_x": float(self.oa_x),
            "oa_y": float(self.oa_y),
            "oa_z": float(self.oa_z),
            "freq_resolution": float(self.freq_resolution),
            "fft_length": self.fft_length,
            "report_len": self.report_len,
            "reserved_bytes": self.reserved_bytes.hex(),
            "acceleration_data": {
                "x": self.acceleration_data["x"].tolist(),
                "y": self.acceleration_data["y"].tolist(),
                "z": self.acceleration_data["z"].tolist(),
            },
            "velocity_data": {
                "x": self.velocity_data["x"].tolist(),
                "y": self.velocity_data["y"].tolist(),
                "z": self.velocity_data["z"].tolist(),
            },
            "padded_acceleration_data": {
                "x": self.acc_x_padded.tolist(),
                "y": self.acc_y_padded.tolist(),
                "z": self.acc_z_padded.tolist(),
            },
            "padded_velocity_data": {
                "x": self.vec_x_padded.tolist(),
                "y": self.vec_y_padded.tolist(),
                "z": self.vec_z_padded.tolist(),
            },
        }

    def plot(self):
        """
        Plot FFT diagrams for acceleration and velocity data.

        Creates a figure with 3 subplots (one for each axis) showing:
        - RMS Acceleration (g)
        - RMS Velocity (mm/s)
        """

        # Calculate frequencies array
        frequencies = np.arange(self.fft_length) * self.freq_resolution

        # Calculate FFT values for acceleration data
        fft_values_acc = {
            "x": np.fft.fft(self.acc_x_padded),
            "y": np.fft.fft(self.acc_y_padded),
            "z": np.fft.fft(self.acc_z_padded),
        }

        # Calculate FFT values for velocity data
        fft_values_vec = {
            "x": np.fft.fft(self.vec_x_padded),
            "y": np.fft.fft(self.vec_y_padded),
            "z": np.fft.fft(self.vec_z_padded),
        }

        # Create subplot figure
        fig, axs = plt.subplots(3, 1, figsize=(10, 15))

        # Plot each axis
        for i, axis in enumerate(["x", "y", "z"]):
            axs[i].plot(
                frequencies[: self.fft_length // 2],
                np.abs(fft_values_acc[axis])[: self.fft_length // 2],
                label="RMS Acceleration g",
            )
            axs[i].plot(
                frequencies[: self.fft_length // 2],
                np.abs(fft_values_vec[axis])[: self.fft_length // 2],
                label="RMS Velocity mm/s",
            )
            axs[i].set_title(f"FFT of Acceleration and Velocity Data ({axis}-axis)")
            axs[i].set_xlabel("Frequency (Hz)")
            axs[i].set_ylabel("Magnitude")
            axs[i].grid()
            axs[i].legend()

        plt.tight_layout()
        plt.show()


# -----------------------------------------------------------------------------
# Extract all values
# -----------------------------------------------------------------------------
# Data type
# data_type_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=30, length=1))
# data_type = pp.hex_to_number(
#     HexToNumberInput(hex_str=data_type_hex, data_type="int", endian="little")
# )
# print(f"Data type: {data_type}")
#
# # Data Length
# data_length_hex = pp.extract_hex(
#     BytesExtractInput(data=file_bytes, offset=31, length=4)
# )
# data_length = pp.hex_to_number(
#     HexToNumberInput(hex_str=data_length_hex, data_type="int", endian="big")
# )
# print(f"Data length: {data_length}")
#
# # Timestamp
# timestamp_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=35, length=8))
# timestamp = pp.hex_to_number(
#     HexToNumberInput(hex_str=timestamp_hex, data_type="int", endian="little")
# )
# normal_datetime = datetime.fromtimestamp(timestamp)
# print(f"Normal DateTime: {normal_datetime}")
#
# # FFT calculation result
# fft_result_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=43, length=1))
# fft_result = pp.hex_to_number(
#     HexToNumberInput(hex_str=fft_result_hex, data_type="int", endian="little")
# )
# print(f"FFT calculation result: {fft_result}")
#
# # Battery level
# battery_level_hex = pp.extract_hex(
#     BytesExtractInput(data=file_bytes, offset=44, length=1)
# )
# battery_level = pp.hex_to_number(
#     HexToNumberInput(hex_str=battery_level_hex, data_type="int", endian="little")
# )
# print(f"Battery level: {battery_level}")
#
# # ADC (average)
# adcavg_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=45, length=2))
# adcavg = pp.hex_to_number(
#     HexToNumberInput(hex_str=adcavg_hex, data_type="int", endian="little")
# )
# print(f"ADC (average): {adcavg}")
#
# # ADC (last)
# adclast_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=47, length=2))
# adclast = pp.hex_to_number(
#     HexToNumberInput(hex_str=adclast_hex, data_type="int", endian="little")
# )
# print(f"ADC (last): {adclast}")
#
# # Temperature
# temperature_hex = pp.extract_hex(
#     BytesExtractInput(data=file_bytes, offset=49, length=2)
# )
# temperature = pp.hex_to_number(
#     HexToNumberInput(hex_str=temperature_hex, data_type="int", endian="little")
# )
# print(f"Temperature: {temperature}")
#
# # OA (x axis) - velocity mm/s
# oa_x_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=51, length=4))
# oa_x = pp.hex_to_number(
#     HexToNumberInput(hex_str=oa_x_hex, data_type="float", endian="little")
# )
# print(f"OA (x axis) - velocity mm/s: {oa_x}")
#
# # OA (y axis) - velocity mm/s
# oa_y_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=55, length=4))
# oa_y = pp.hex_to_number(
#     HexToNumberInput(hex_str=oa_y_hex, data_type="float", endian="little")
# )
# print(f"OA (y axis) - velocity mm/s: {oa_y}")
#
# # OA (z axis) - velocity mm/s
# oa_z_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=59, length=4))
# oa_z = pp.hex_to_number(
#     HexToNumberInput(hex_str=oa_z_hex, data_type="float", endian="little")
# )
# print(f"OA (z axis) - velocity mm/s: {oa_z}")
#
# # Frequency resolution
# freq_resolution_hex = pp.extract_hex(
#     BytesExtractInput(data=file_bytes, offset=63, length=4)
# )
# freq_resolution = pp.hex_to_number(
#     HexToNumberInput(hex_str=freq_resolution_hex, data_type="float", endian="little")
# )
# print(f"Frequency resolution: {freq_resolution}")
#
# # FFT length
# fft_length_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=67, length=4))
# fft_length = pp.hex_to_number(
#     HexToNumberInput(hex_str=fft_length_hex, data_type="int", endian="big")
# )
# print(f"FFT length: {fft_length}")
#
# # ReportLen
# report_len_hex = pp.extract_hex(BytesExtractInput(data=file_bytes, offset=71, length=4))
# report_len = pp.hex_to_number(
#     HexToNumberInput(hex_str=report_len_hex, data_type="int", endian="big")
# )
# print(f"ReportLen: {report_len}")
#
# # Reserved bytes
# reserved_bytes_hex = pp.extract_hex(
#     BytesExtractInput(data=file_bytes, offset=75, length=5)
# )
#
# # Acc (x axis)
# acc_x_values = np.zeros(int(report_len))
# for i in range(int(report_len)):
#     offset = 80 + i * 4
#     acc_x_hex = pp.extract_hex(
#         BytesExtractInput(data=file_bytes, offset=offset, length=4)
#     )
#     acc_x_value = pp.hex_to_number(
#         HexToNumberInput(hex_str=acc_x_hex, data_type="float", endian="little")
#     )
#     acc_x_values[i] = acc_x_value
# print(f"Acc (x axis) - shape: {acc_x_values.shape} acceleration values: {acc_x_values}")
#
# # Acc (y axis)
# acc_y_values = np.zeros(int(report_len))
# for i in range(int(report_len)):
#     offset = int(80 + report_len * 4 + i * 4)
#     acc_y_hex = pp.extract_hex(
#         BytesExtractInput(data=file_bytes, offset=offset, length=4)
#     )
#     acc_y_value = pp.hex_to_number(
#         HexToNumberInput(hex_str=acc_y_hex, data_type="float", endian="little")
#     )
#     acc_y_values[i] = acc_y_value
# print(f"Acc (y axis) - shape: {acc_y_values.shape} acceleration values: {acc_y_values}")
#
# # Acc (z axis)
# acc_z_values = np.zeros(int(report_len))
# for i in range(int(report_len)):
#     offset = int(80 + 2 * report_len * 4 + i * 4)
#     acc_z_hex = pp.extract_hex(
#         BytesExtractInput(data=file_bytes, offset=offset, length=4)
#     )
#     acc_z_value = pp.hex_to_number(
#         HexToNumberInput(hex_str=acc_z_hex, data_type="float", endian="little")
#     )
#     acc_z_values[i] = acc_z_value
# print(f"Acc (z axis) - shape {acc_z_values.shape} acceleration values: {acc_z_values}")
#
# # Vec (x axis)
# vec_x_values = np.zeros(int(report_len))
# for i in range(int(report_len)):
#     offset = int(80 + 3 * report_len * 4 + i * 4)
#     vec_x_hex = pp.extract_hex(
#         BytesExtractInput(data=file_bytes, offset=offset, length=4)
#     )
#     vec_x_value = pp.hex_to_number(
#         HexToNumberInput(hex_str=vec_x_hex, data_type="float", endian="little")
#     )
#     vec_x_values[i] = vec_x_value
# print(f"Vec (x axis) - shape {vec_x_values.shape} velocity values: {vec_x_values}")
#
# # Vec (y axis)
# vec_y_values = np.zeros(int(report_len))
# for i in range(int(report_len)):
#     offset = int(80 + 4 * report_len * 4 + i * 4)
#     vec_y_hex = pp.extract_hex(
#         BytesExtractInput(data=file_bytes, offset=offset, length=4)
#     )
#     vec_y_value = pp.hex_to_number(
#         HexToNumberInput(hex_str=vec_y_hex, data_type="float", endian="little")
#     )
#     vec_y_values[i] = vec_y_value
# print(f"Vec (y axis) - shape {vec_y_values.shape} velocity values: {vec_y_values}")
#
# # Vec (z axis)
# vec_z_values = np.zeros(int(report_len))
# for i in range(int(report_len)):
#     offset = int(80 + 5 * report_len * 4 + i * 4)
#     vec_z_hex = pp.extract_hex(
#         BytesExtractInput(data=file_bytes, offset=offset, length=4)
#     )
#     vec_z_value = pp.hex_to_number(
#         HexToNumberInput(hex_str=vec_z_hex, data_type="float", endian="little")
#     )
#     vec_z_values[i] = vec_z_value
# print(f"Vec (z axis) - shape {vec_z_values.shape} velocity values: {vec_z_values}")
#
# # Velocity data - Fixed the z-axis assignment
# velocity_data = {"x": vec_x_values, "y": vec_y_values, "z": vec_z_values}
#
#
# # -----------------------------------------------------------------------------
# # Just to make sure there is nothing else left
# # -----------------------------------------------------------------------------
# def get_file_size(file_path):
#     return os.path.getsize(file_path)
#
#
# last_z_offset = 80 + 6 * report_len * 4  # Starting offset for Vec(z) values
# file_size = get_file_size(binary_file_path)
# remaining_data = file_size - last_z_offset
#
# if remaining_data > 0:
#     print(f"There is {remaining_data} bytes of remaining data after the z-axis values.")
# else:
#     print("There is no remaining data after the z-axis values. Hoorey 😃!")
#
# print(
#     "\n--------------------------\n"
#     + "Plotting the FFT diagram..."
#     + "\n--------------------------\n"
# )
#
# # -----------------------------------------------------------------------------
# # Plot the FFT diagram for acceleration data
# # -----------------------------------------------------------------------------
# acc_x_padded = np.pad(
#     acc_x_values, [(0, int(fft_length - len(acc_x_values)))], mode="constant"
# )
# acc_y_padded = np.pad(
#     acc_y_values, [(0, int(fft_length - len(acc_y_values)))], mode="constant"
# )
# acc_z_padded = np.pad(
#     acc_z_values, [(0, int(fft_length - len(acc_z_values)))], mode="constant"
# )
#
# acceleration_data = {"x": acc_x_padded, "y": acc_y_padded, "z": acc_z_padded}
# fft_values_acc = {
#     "x": np.fft.fft(acceleration_data["x"]),
#     "y": np.fft.fft(acceleration_data["y"]),
#     "z": np.fft.fft(acceleration_data["z"]),
# }
# for axis in ["x", "y", "z"]:
#     print(f"FFT values acc shape ({axis}): {fft_values_acc[axis].shape}")
# print(f"FFT values acc: {fft_values_acc}")
#
# frequencies = np.arange(fft_length) * freq_resolution
# print(f"Frequencies shape: {frequencies.shape}; value: {frequencies}")
#
# vec_x_padded = np.pad(
#     vec_x_values, [(0, int(fft_length - len(vec_x_values)))], mode="constant"
# )
# vec_y_padded = np.pad(
#     vec_y_values, [(0, int(fft_length - len(vec_y_values)))], mode="constant"
# )
# vec_z_padded = np.pad(
#     vec_z_values, [(0, int(fft_length - len(vec_z_values)))], mode="constant"
# )
#
# velocity_data = {"x": vec_x_padded, "y": vec_y_padded, "z": vec_z_padded}
# fft_values_vec = {
#     "x": np.fft.fft(velocity_data["x"]),
#     "y": np.fft.fft(velocity_data["y"]),
#     "z": np.fft.fft(velocity_data["z"]),
# }
# for axis in ["x", "y", "z"]:
#     print(f"FFT values vec shape ({axis}): {fft_values_vec[axis].shape}")
# print(f"FFT values vec: {fft_values_vec}")
#
# fig, axs = plt.subplots(3, 1, figsize=(10, 15))
# for i, axis in enumerate(["x", "y", "z"]):
#     axs[i].plot(
#         frequencies[: fft_length // 2],
#         np.abs(fft_values_acc[axis])[: fft_length // 2],
#         label="RMS Acceleration g",
#     )
#     axs[i].plot(
#         frequencies[: fft_length // 2],
#         np.abs(fft_values_vec[axis])[: fft_length // 2],
#         label="RMS Velocity mm/s",
#     )
#     axs[i].set_title(f"FFT of Acceleration and Velocity Data ({axis}-axis)")
#     axs[i].set_xlabel("Frequency (Hz)")
#     axs[i].set_ylabel("Magnitude")
#     axs[i].grid()
#     axs[i].legend()
#
# plt.tight_layout()
# plt.show()
