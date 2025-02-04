from asusiot_aissens_mqtt.plugins.interface import Plugin


class Stdout(Plugin):
    def input(self, topic: str, payload: bytes, userdata: None) -> None:
        print(f"Received message on topic {topic}")
        print(f"Payload (hex): {payload.hex()}")  # Print hex representation instead
        try:
            # Try UTF-8 decode, but fallback to hex if it fails
            print(f"Payload (text): {payload.decode('utf-8')}")
        except UnicodeDecodeError:
            print("Payload is not UTF-8 encoded text")
