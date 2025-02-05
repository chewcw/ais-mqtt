from typing import Literal

DataTypeName = Literal[
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
    "Reserved"
]

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
