import logging
import os
from pathlib import Path
from typing import Dict, List, Any

import yaml
import psycopg2
from psycopg2 import sql

from src.tools.tools_interface import OutputInterface

logger = logging.getLogger(__name__)


class PostgreSQL(OutputInterface):
    def __init__(self) -> None:
        self.config = self._load_config()

        if not self.config.get("tables"):
            raise ValueError("No table schema defined in the configuration")

        # Get connection parameters
        db_config = self.config.get("database", {})
        self.connection_params = {
            "host": os.path.expandvars(db_config.get("host", "localhost")),
            "port": db_config.get("port", 5432),
            "database": os.path.expandvars(db_config.get("database", "postgres")),
            "user": os.path.expandvars(db_config.get("user", "postgres")),
            "password": os.path.expandvars(db_config.get("password", "")),
        }

        logger.info(
            f"Connecting to PostgreSQL database: {self.connection_params['database']} "
            f"on {self.connection_params['host']}:{self.connection_params['port']}"
        )

        try:
            self.conn = psycopg2.connect(**self.connection_params)
            logger.info("Connected to PostgreSQL database successfully")
        except psycopg2.Error as e:
            logger.error(f"Failed to connect to PostgreSQL database: {e}")
            raise

        self.tables: Dict[str, List[dict]] = {
            table["name"]: table["columns"] for table in self.config["tables"]
        }
        self._init_tables()

    def _load_config(self) -> dict:
        # Try to load configuration from the config directory
        config_path = Path(__file__).parent / "config" / "config.yaml"
        example_config_path = Path(__file__).parent / "config" / "config_example.yaml"

        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f)
                logger.info("Loaded configuration from config/config.yaml")
                return config
            except Exception as e:
                logger.warning(f"Failed to load config/config.yaml: {e}")

        try:
            with open(example_config_path, "r") as f:
                config = yaml.safe_load(f)
            logger.info("Loaded configuration from config/config_example.yaml")
            return config
        except Exception as e:
            raise ValueError(f"Failed to load any configuration: {e}")

    def _init_tables(self) -> None:
        cursor = self.conn.cursor()

        for table_name, columns in self.tables.items():
            # Build column definitions
            column_defs = []
            for col in columns:
                col_name = col["name"]
                col_type = col["type"]  # Use PostgreSQL native type directly
                column_defs.append(f"{col_name} {col_type}")

            # Add primary key id column
            column_defs.insert(0, "id SERIAL PRIMARY KEY")

            # Create table using sql module for safe table name quoting
            table_query = sql.SQL("""
                CREATE TABLE IF NOT EXISTS {} (
                    {}
                )
            """).format(
                sql.Identifier(table_name),
                sql.SQL(", ").join(map(sql.SQL, column_defs)),
            )

            cursor.execute(table_query)

        self.conn.commit()

    def _get_pg_type(self, pg_type: str) -> str:
        """Normalize PostgreSQL type string"""
        return pg_type.upper()

    def _pg_type_check(self, value: Any, col_type: str) -> bool:
        """Check if value matches expected PostgreSQL type"""
        col_type = col_type.upper()

        if value is None:
            return True  # NULL values are allowed for any type

        if (
            col_type.startswith("TEXT")
            or col_type.startswith("VARCHAR")
            or col_type.startswith("CHAR")
        ):
            return isinstance(value, str)
        elif (
            col_type.startswith("INTEGER")
            or col_type.startswith("SMALLINT")
            or col_type.startswith("BIGINT")
            or col_type.startswith("SERIAL")
        ):
            return isinstance(value, int)
        elif (
            col_type.startswith("DOUBLE PRECISION")
            or col_type.startswith("REAL")
            or col_type.startswith("NUMERIC")
            or col_type.startswith("DECIMAL")
        ):
            return isinstance(value, (float, int))
        elif col_type.startswith("BYTEA"):
            return isinstance(value, bytes)
        elif (
            col_type.startswith("TIMESTAMP")
            or col_type.startswith("DATE")
            or col_type.startswith("TIME")
        ):
            return isinstance(value, str)  # Accept string for time-related types
        elif col_type.startswith("BOOLEAN"):
            return isinstance(value, bool)
        elif col_type.startswith("JSON") or col_type.startswith("JSONB"):
            return isinstance(value, (dict, list, str))
        else:
            return True  # Unknown type, assume it's valid

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

            if not self._pg_type_check(value, col_type):
                raise TypeError(
                    f"Column '{col_name}' expects {col_type} but got {type(value)}"
                )

        # Prepare values dictionary
        values = {}

        # Build values dictionary according to schema
        for column in columns:
            col_name = column["name"]
            values[col_name] = kwargs[col_name]

        # Build columns and placeholders for SQL query
        columns_list = [col["name"] for col in columns]
        columns_sql = sql.SQL(", ").join(map(sql.Identifier, columns_list))
        placeholders_sql = sql.SQL(", ").join(sql.Placeholder() * len(columns_list))

        # Build SQL query using sql module for safe quoting
        insert_sql = sql.SQL("""
        INSERT INTO {} ({})
        VALUES ({})
        """).format(sql.Identifier(name), columns_sql, placeholders_sql)

        # Get values in the same order as columns
        values_tuple = tuple(values[col["name"]] for col in columns)

        # Execute insert
        cursor.execute(insert_sql, values_tuple)
        self.conn.commit()

    def close(self) -> None:
        if hasattr(self, "conn") and self.conn is not None:
            self.conn.close()
            logger.info("PostgreSQL connection closed")
