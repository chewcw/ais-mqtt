from asusiot_aissens_mqtt.tools.tools_interface import OutputInterface


class Stdout(OutputInterface):
    def __init__(self) -> None:
        pass

    def output(self, name: str, *args, **kwargs) -> None:
        print(f"Name: {name}")
        print(f"Data: {kwargs}")
