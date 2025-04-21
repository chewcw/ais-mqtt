import json
from dataclasses import dataclass
from datetime import datetime
from typing import cast

import matplotlib.pyplot as plt
import numpy as np

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
class PacketFFT:
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
        adcavg (float): Average ADC value
        adclast (float): Last ADC value
        temperature (float): Temperature reading
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
        freqs (np.ndarray): Frequency values for FFT
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
    fft_result: int
    battery_level: int
    adcavg: float
    adclast: float
    temperature: float
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
    freqs: np.ndarray


class FFTDecodeError(Exception):
    def __init__(self, field_name: str, error: Exception):
        self.field_name = field_name
        self.error = error
        super().__init__(f"Failed to decode field '{field_name}': {str(error)}")


class PacketFFTDecoder:
    def __init__(self, file_bytes: bytes):
        """
        Initialize the FFT packet decoder.

        Args:
            file_bytes (bytes): Raw binary data to be decoded
        """
        self.file_bytes = file_bytes
        self.fft_packet: PacketFFT | None = None

    def decode(self) -> PacketFFT:
        """
        Decode the binary data into a structured FFT packet.
        Raises FFTDecodeError with specific field information on failure.
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
            raise FFTDecodeError("data_type", e)

        try:
            data_type_name = cast(
                DataTypeName, DATA_TYPE_MAP.get(data_type, "Reserved")
            )
        except Exception as e:
            raise FFTDecodeError("data_type_name", e)

        try:
            data_length_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=1, length=4)
            )
            data_length = pp.hex_to_number(
                HexToNumberInput(hex_str=data_length_hex, data_type="int", endian="big")
            )
        except Exception as e:
            raise FFTDecodeError("data_length", e)

        try:
            timestamp_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=5, length=8)
            )
            timestamp = pp.hex_to_timestamp(
                HexToTimestampInput(hex_str=timestamp_hex, endian="little")
            )
        except Exception as e:
            raise FFTDecodeError("timestamp", e)

        try:
            fft_result_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=13, length=1)
            )
            fft_result = pp.hex_to_number(
                HexToNumberInput(
                    hex_str=fft_result_hex, data_type="int", endian="little"
                )
            )
        except Exception as e:
            raise FFTDecodeError("fft_result", e)

        try:
            battery_level_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=14, length=1)
            )
            battery_level = pp.hex_to_number(
                HexToNumberInput(
                    hex_str=battery_level_hex, data_type="int", endian="little"
                )
            )
        except Exception as e:
            raise FFTDecodeError("battery_level", e)

        try:
            adcavg_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=15, length=2)
            )
            adcavg = pp.hex_to_number(
                HexToNumberInput(hex_str=adcavg_hex, data_type="int", endian="little")
            )
            adcavg = adcavg / 1000
        except Exception as e:
            raise FFTDecodeError("adcavg", e)

        try:
            adclast_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=17, length=2)
            )
            adclast = pp.hex_to_number(
                HexToNumberInput(hex_str=adclast_hex, data_type="int", endian="little")
            )
            adclast = adclast / 1000
        except Exception as e:
            raise FFTDecodeError("adclast", e)

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
            raise FFTDecodeError("temperature", e)

        try:
            oa_x_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=21, length=4)
            )
            oa_x = pp.hex_to_number(
                HexToNumberInput(hex_str=oa_x_hex, data_type="float", endian="little")
            )
        except Exception as e:
            raise FFTDecodeError("oa_x", e)

        try:
            oa_y_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=25, length=4)
            )
            oa_y = pp.hex_to_number(
                HexToNumberInput(hex_str=oa_y_hex, data_type="float", endian="little")
            )
        except Exception as e:
            raise FFTDecodeError("oa_y", e)

        try:
            oa_z_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=29, length=4)
            )
            oa_z = pp.hex_to_number(
                HexToNumberInput(hex_str=oa_z_hex, data_type="float", endian="little")
            )
        except Exception as e:
            raise FFTDecodeError("oa_z", e)

        try:
            freq_resolution_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=33, length=4)
            )
            freq_resolution = pp.hex_to_number(
                HexToNumberInput(
                    hex_str=freq_resolution_hex, data_type="float", endian="little"
                )
            )
        except Exception as e:
            raise FFTDecodeError("freq_resolution", e)

        try:
            fft_length_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=37, length=4)
            )
            fft_length = pp.hex_to_number(
                HexToNumberInput(hex_str=fft_length_hex, data_type="int", endian="big")
            )
        except Exception as e:
            raise FFTDecodeError("fft_length", e)

        try:
            report_len_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=41, length=4)
            )
            report_len = int(
                pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=report_len_hex, data_type="int", endian="big"
                    )
                )
            )
        except Exception as e:
            raise FFTDecodeError("report_len", e)

        try:
            reserved_bytes_hex = pp.extract_hex(
                BytesExtractInput(data=self.file_bytes, offset=45, length=5)
            )
            reserved_bytes = bytes.fromhex(reserved_bytes_hex)
        except Exception as e:
            raise FFTDecodeError("reserved_bytes", e)

        try:
            acc_x_values = np.zeros(report_len)
            for i in range(report_len):
                offset = 50 + i * 4
                acc_x_hex = pp.extract_hex(
                    BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
                )
                acc_x_values[i] = pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=acc_x_hex, data_type="float", endian="little"
                    )
                )
        except Exception as e:
            raise FFTDecodeError("acc_x_values", e)

        try:
            acc_y_values = np.zeros(report_len)
            for i in range(report_len):
                offset = int(50 + report_len * 4 + i * 4)
                acc_y_hex = pp.extract_hex(
                    BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
                )
                acc_y_values[i] = pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=acc_y_hex, data_type="float", endian="little"
                    )
                )
        except Exception as e:
            raise FFTDecodeError("acc_y_values", e)

        try:
            acc_z_values = np.zeros(report_len)
            for i in range(report_len):
                offset = int(50 + 2 * report_len * 4 + i * 4)
                acc_z_hex = pp.extract_hex(
                    BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
                )
                acc_z_values[i] = pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=acc_z_hex, data_type="float", endian="little"
                    )
                )
        except Exception as e:
            raise FFTDecodeError("acc_z_values", e)

        acceleration_data = {
            "x": acc_x_values,
            "y": acc_y_values,
            "z": acc_z_values,
        }

        try:
            vec_x_values = np.zeros(report_len)
            for i in range(report_len):
                offset = int(50 + 3 * report_len * 4 + i * 4)
                vec_x_hex = pp.extract_hex(
                    BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
                )
                vec_x_values[i] = pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=vec_x_hex, data_type="float", endian="little"
                    )
                )
        except Exception as e:
            raise FFTDecodeError("vec_x_values", e)

        try:
            vec_y_values = np.zeros(report_len)
            for i in range(report_len):
                offset = int(50 + 4 * report_len * 4 + i * 4)
                vec_y_hex = pp.extract_hex(
                    BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
                )
                vec_y_values[i] = pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=vec_y_hex, data_type="float", endian="little"
                    )
                )
        except Exception as e:
            raise FFTDecodeError("vec_y_values", e)

        try:
            vec_z_values = np.zeros(report_len)
            for i in range(report_len):
                offset = int(50 + 5 * report_len * 4 + i * 4)
                vec_z_hex = pp.extract_hex(
                    BytesExtractInput(data=self.file_bytes, offset=offset, length=4)
                )
                vec_z_values[i] = pp.hex_to_number(
                    HexToNumberInput(
                        hex_str=vec_z_hex, data_type="float", endian="little"
                    )
                )
        except Exception as e:
            raise FFTDecodeError("vec_z_values", e)

        velocity_data = {"x": vec_x_values, "y": vec_y_values, "z": vec_z_values}

        try:
            acc_x_padded = np.pad(
                acceleration_data["x"],
                [(0, int(fft_length - len(acceleration_data["x"])))],
                mode="constant",
            )
            acc_y_padded = np.pad(
                acceleration_data["y"],
                [(0, int(fft_length - len(acceleration_data["y"])))],
                mode="constant",
            )
            acc_z_padded = np.pad(
                acceleration_data["z"],
                [(0, int(fft_length - len(acceleration_data["z"])))],
                mode="constant",
            )
        except Exception as e:
            raise FFTDecodeError("acceleration_padding", e)

        try:
            vec_x_padded = np.pad(
                velocity_data["x"],
                [(0, int(fft_length - len(velocity_data["x"])))],
                mode="constant",
            )
            vec_y_padded = np.pad(
                velocity_data["y"],
                [(0, int(fft_length - len(velocity_data["y"])))],
                mode="constant",
            )
            vec_z_padded = np.pad(
                velocity_data["z"],
                [(0, int(fft_length - len(velocity_data["z"])))],
                mode="constant",
            )
        except Exception as e:
            raise FFTDecodeError("velocity_padding", e)

        self.fft_packet = PacketFFT(
            data_type=int(data_type),
            data_type_name=data_type_name,
            data_length=int(data_length),
            timestamp=timestamp,
            fft_result=int(fft_result),
            battery_level=int(battery_level),
            adcavg=int(adcavg),
            adclast=int(adclast),
            temperature=temperature,
            oa_x=oa_x,
            oa_y=oa_y,
            oa_z=oa_z,
            freq_resolution=freq_resolution,
            fft_length=int(fft_length),
            report_len=report_len,
            reserved_bytes=reserved_bytes,
            _acc_x_values=acceleration_data["x"],
            _acc_y_values=acceleration_data["y"],
            _acc_z_values=acceleration_data["z"],
            _vec_x_values=velocity_data["x"],
            _vec_y_values=velocity_data["y"],
            _vec_z_values=velocity_data["z"],
            acc_x_padded=acc_x_padded,
            acc_y_padded=acc_y_padded,
            acc_z_padded=acc_z_padded,
            vec_x_padded=vec_x_padded,
            vec_y_padded=vec_y_padded,
            vec_z_padded=vec_z_padded,
            velocity_data=velocity_data,
            acceleration_data=acceleration_data,
            freqs=np.arange(fft_length) * freq_resolution,
        )

        return self.fft_packet

    def to_json(self) -> str:
        """
        Converts the FFTPacket instance to a JSON-serializable dictionary.

        Returns:
            dict: A dictionary containing all FFTPacket data in a JSON-serializable format
        """

        if self.fft_packet is None:
            raise ValueError(
                "No FFT packet data available. Please decode the packet first."
            )

        return json.dumps({
            "data_type": self.fft_packet.data_type,
            "data_type_name": self.fft_packet.data_type_name,
            "timestamp": self.fft_packet.timestamp.isoformat(),
            "fft_result": self.fft_packet.fft_result,
            "battery_level": self.fft_packet.battery_level,
            "adcavg": self.fft_packet.adcavg,
            "adclast": self.fft_packet.adclast,
            "temperature": self.fft_packet.temperature,
            "oa_x": float(self.fft_packet.oa_x),
            "oa_y": float(self.fft_packet.oa_y),
            "oa_z": float(self.fft_packet.oa_z),
            "freq_resolution": float(self.fft_packet.freq_resolution),
            "fft_length": self.fft_packet.fft_length,
            "padded_acceleration_data": {
                "x": self.fft_packet.acc_x_padded.tolist(),
                "y": self.fft_packet.acc_y_padded.tolist(),
                "z": self.fft_packet.acc_z_padded.tolist(),
            },
            "padded_velocity_data": {
                "x": self.fft_packet.vec_x_padded.tolist(),
                "y": self.fft_packet.vec_y_padded.tolist(),
                "z": self.fft_packet.vec_z_padded.tolist(),
            },
            "freqs": self.fft_packet.freqs.tolist(),
        })

    def plot(self):
        """
        Plot FFT diagrams for acceleration and velocity data.

        Creates a figure with 3 subplots (one for each axis) showing:
        - RMS Acceleration (g)
        - RMS Velocity (mm/s)
        """

        if self.fft_packet is None:
            raise ValueError(
                "No FFT packet data available. Please decode the packet first."
            )

        # Calculate frequencies array
        frequencies = (
            np.arange(self.fft_packet.fft_length) * self.fft_packet.freq_resolution
        )

        # Calculate FFT values for acceleration data
        fft_values_acc = {
            "x": np.fft.fft(self.fft_packet.acc_x_padded),
            "y": np.fft.fft(self.fft_packet.acc_y_padded),
            "z": np.fft.fft(self.fft_packet.acc_z_padded),
        }

        # Calculate FFT values for velocity data
        fft_values_vec = {
            "x": np.fft.fft(self.fft_packet.vec_x_padded),
            "y": np.fft.fft(self.fft_packet.vec_y_padded),
            "z": np.fft.fft(self.fft_packet.vec_z_padded),
        }

        # Create subplot figure
        fig, axs = plt.subplots(3, 1, figsize=(10, 15))

        # Plot each axis
        for i, axis in enumerate(["x", "y", "z"]):
            axs[i].plot(
                frequencies[: self.fft_packet.fft_length // 2],
                np.abs(fft_values_acc[axis])[: self.fft_packet.fft_length // 2],
                label="RMS Acceleration g",
            )
            axs[i].plot(
                frequencies[: self.fft_packet.fft_length // 2],
                np.abs(fft_values_vec[axis])[: self.fft_packet.fft_length // 2],
                label="RMS Velocity mm/s",
            )
            axs[i].set_title(f"FFT of Acceleration and Velocity Data ({axis}-axis)")
            axs[i].set_xlabel("Frequency (Hz)")
            axs[i].set_ylabel("Magnitude")
            axs[i].grid()
            axs[i].legend()

        plt.tight_layout()
        plt.show()
