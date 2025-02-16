from abc import ABC, abstractmethod


class OutputInterface(ABC):
    @abstractmethod
    def output(self, name: str, *args, **kwargs) -> None:
        """
        Output data to target.

        Args:
            name (str): The unique identifier for the output (e.g. table column name).
            *args: Variable length argument list.
                  Additional positional arguments that may be needed by implementations.
            **kwargs: Arbitrary keyword arguments.
                     Additional named parameters that may be needed by implementations.

        Returns:
            None

        Example:
            >>> output("sensor_data", value=23.5, unit="celsius")
                     # where "sensor_data" represents the table column to store the value
        """
        pass
