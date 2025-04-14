from pathlib import Path

from src.plugins.aissens.packet import Packet


def main():
    binary_data = Path(__file__).parent / "./report_fft_data"
    with open(binary_data, "rb") as file:
        payload = file.read()

    packet = Packet()
    packet.input("S9IMP6000067BSF/report", payload, None)

