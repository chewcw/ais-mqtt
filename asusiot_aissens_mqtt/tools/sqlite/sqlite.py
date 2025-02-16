import logging
import os
import sqlite3
from pathlib import Path
from typing import Dict, List

import yaml

from asusiot_aissens_mqtt.tools.tools_interface import OutputInterface

logger = logging.getLogger(__name__)


class Sqlite(OutputInterface):
    def __init__(self) -> None:
        self.config = self._load_config()

        if not self.config.get("tables"):
            raise ValueError("No table schema defined in the configuration")

        # Get absolute path for database
        db_path = self.config.get("database", {}).get("path", "data.db")
        db_path = os.path.abspath(db_path)
        logger.info(f"Using database path: {db_path}")

        # Create directory if it doesn't exist
        db_dir = os.path.dirname(db_path)
        if db_dir:
            try:
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"Directory exists or created: {db_dir}")
            except OSError as e:
                logger.error(f"Failed to create directory {db_dir}: {e}")
                raise

        # Ensure directory is writable
        if not os.access(db_dir, os.W_OK):
            logger.error(f"No write permission in directory: {db_dir}")
            raise PermissionError(f"No write permission in directory: {db_dir}")

        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.execute("PRAGMA journal_mode=WAL")  # Use Write-Ahead Logging for better concurrent access
            logger.info(f"Connected to database: {db_path}")
            if not os.path.exists(db_path):
                logger.info("New database file created")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database {db_path}: {e}")
            raise

        self.tables: Dict[str, List[dict]] = {
            table["name"]: table["columns"] for table in self.config["tables"]
        }
        self._init_tables()

    def _load_config(self) -> dict:
        # Try to load configuration
        config_path = Path(__file__).parent / "config.yaml"
        example_config_path = Path(__file__).parent / "config_example.yaml"

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                logger.info("Loaded configuration from config.yaml")
            except Exception as e:
                logger.warning(f"Failed to load config.yaml: {e}")

        try:
            with open(example_config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info("Loaded configuration from config_example.yaml")
            return config
        except Exception as e:
            raise ValueError(f"Failed to load any configuration: {e}")

    def _init_tables(self) -> None:
        cursor = self.conn.cursor()

        for table_name, columns in self.tables.items():
            # Build column definitions
            column_defs = [f"{col['name']} {col['type']}" for col in columns]
            # Add primary key id column
            column_defs.insert(0, "id INTEGER PRIMARY KEY AUTOINCREMENT")

            # Create table
            cursor.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {", ".join(column_defs)}
                )
                """
            )

        self.conn.commit()

    def output(self, name: str, *args, **kwargs) -> None:
        if name not in self.tables:
            raise ValueError(f"Table '{name}' not defined in the configuration")

        cursor = self.conn.cursor()

        # Get schema columns (excluding id as it's auto-incrementing)
        columns = [col for col in self.tables[name] if col["name"] != "id"]

        # Validate all required columns are present in kwargs
        for column in columns:
            col_name = column["name"]
            col_type = column["type"].upper()

            if col_name not in kwargs:
                raise ValueError(
                    f"Missing required column '{col_name}' in kwargs for table '{name}'"
                )

            # Validate type
            value = kwargs[col_name]

            # Type validation
            if col_type.startswith("TEXT"):
                if not isinstance(value, (str, type(None))):
                    raise TypeError(
                        f"Column '{col_name}' expects TEXT but got {type(value)}"
                    )
            elif col_type.startswith("INTEGER"):
                if not isinstance(value, (int, type(None))):
                    raise TypeError(
                        f"Column '{col_name}' expects INTEGER but got {type(value)}"
                    )
            elif col_type.startswith("REAL"):
                if not isinstance(value, (float, int, type(None))):
                    raise TypeError(
                        f"Column '{col_name}' expects REAL but got {type(value)}"
                    )
            elif col_type.startswith("BLOB"):
                if not isinstance(value, (bytes, type(None))):
                    raise TypeError(
                        f"Column '{col_name}' expects BLOB but got {type(value)}"
                    )
            else:
                raise ValueError(f"Unsupported column type: {col_type}")

        # Prepare values dictionary
        values = {}

        # Build values dictionary according to schema
        for column in columns:
            col_name = column["name"]
            values[col_name] = kwargs[col_name]

        # Build SQL query
        columns_str = ", ".join(col["name"] for col in columns)
        placeholders = ", ".join(["?" for _ in columns])

        insert_sql = f"""
        INSERT INTO {name} ({columns_str})
        VALUES ({placeholders})
        """

        # Get values in the same order as columns
        values_tuple = tuple(values[col["name"]] for col in columns)

        # Execute insert
        cursor.execute(insert_sql, values_tuple)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
