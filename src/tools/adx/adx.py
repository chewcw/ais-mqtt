import logging
import os
import sys
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from uuid import uuid4
import json
import base64
import zlib

import pandas as pd
import yaml
from azure.kusto.data import DataFormat, KustoClient, KustoConnectionStringBuilder
from azure.kusto.data.data_format import IngestionMappingKind
from azure.kusto.data.exceptions import KustoServiceError
from azure.kusto.ingest import (
    IngestionProperties,
    QueuedIngestClient,
    ReportLevel,
    ReportMethod,
)
from azure.kusto.ingest.status import KustoIngestStatusQueues
from dotenv import load_dotenv

from src.tools.tools_interface import OutputInterface

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


class Adx(OutputInterface):
    def __init__(self) -> None:
        # Load environment variables from .env file
        self._load_env()

        # Load configuration
        self.config = self._load_config()

        if not self.config.get("tables"):
            raise ValueError("No table schema defined in the configuration")

        # Get connection parameters from config
        adx_config = self.config.get("connection", {})

        cluster_uri = os.path.expandvars(adx_config.get("cluster_uri", ""))
        database_name = os.path.expandvars(adx_config.get("database_name", ""))
        ingestion_uri = os.path.expandvars(adx_config.get("data_ingestion_uri", ""))

        # Authentication options (choose one based on config)
        auth_type = adx_config.get("auth_type", "app").lower()

        if auth_type == "app":
            app_id = os.path.expandvars(adx_config.get("app_id", ""))
            app_key = os.path.expandvars(adx_config.get("app_key", ""))
            tenant_id = os.path.expandvars(adx_config.get("tenant_id", ""))

            # Log values after expansion for debugging (without exposing sensitive values)
            logger.debug(f"Using expanded cluster_uri: {cluster_uri}")
            logger.debug(f"Using expanded database_name: {database_name}")
            logger.debug(f"Using expanded app_id: {'*' * 5 if app_id else 'empty'}")
            logger.debug(f"Using expanded app_key: {'*' * 5 if app_key else 'empty'}")
            logger.debug(
                f"Using expanded tenant_id: {'*' * 5 if tenant_id else 'empty'}"
            )

            if not all([cluster_uri, database_name, app_id, app_key, tenant_id]):
                missing_params = []
                if not cluster_uri:
                    missing_params.append("cluster_uri")
                if not database_name:
                    missing_params.append("database_name")
                if not app_id:
                    missing_params.append("app_id")
                if not app_key:
                    missing_params.append("app_key")
                if not tenant_id:
                    missing_params.append("tenant_id")

                logger.error(
                    f"Missing required ADX connection parameters: {', '.join(missing_params)}"
                )
                raise ValueError(
                    f"Missing required ADX connection parameters for app authentication: {', '.join(missing_params)}"
                )

            kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                cluster_uri, app_id, app_key, tenant_id
            )
        # elif auth_type == "managed_identity":
        #     if not all([cluster_uri, database_name]):
        #         raise ValueError("Missing required ADX connection parameters for managed identity authentication")
        #
        #     kcsb = KustoConnectionStringBuilder.with_aad_managed_identity_authentication(
        #         cluster_uri
        #     )
        else:
            raise ValueError(f"Unsupported authentication type: {auth_type}")

        self.database_name = database_name
        self.cluster_uri = cluster_uri

        # Create Kusto clients
        try:
            # For querying data
            self.kusto_client = KustoClient(kcsb)

            logger.debug(f"Using ingestion URI: {ingestion_uri}")

            ingestion_kcsb = None

            # Create a new connection string builder for the ingestion endpoint
            if auth_type == "app":
                ingestion_kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(
                    ingestion_uri, app_id, app_key, tenant_id
                )

            if ingestion_kcsb is None:
                logger.error("Failed to create ingestion connection string builder")
                raise ValueError("Failed to create ingestion connection string builder")

            # Create the ingestion client with the ingestion URI
            self.ingest_client = QueuedIngestClient(ingestion_kcsb)

            logger.info(
                f"Connected to ADX cluster: {cluster_uri}, database: {database_name}"
            )
            logger.info(f"Connected to ADX ingestion endpoint: {ingestion_uri}")
        except Exception as e:
            logger.error(f"Failed to connect to ADX: {e}")
            raise

        # Store table definitions
        self.tables: Dict[str, List[dict]] = {
            table["name"]: table["columns"] for table in self.config["tables"]
        }

        # Create status monitor for ingestion
        self.status_monitor = None
        self.monitor_stop_event = threading.Event()
        self.enable_status_monitoring = self.config.get(
            "enable_status_monitoring", False
        )

        # Start status monitoring if enabled
        if self.enable_status_monitoring:
            self.start_status_monitoring()

        # Initialize tables if configured to do so
        # if self.config.get("create_tables_if_not_exist", False):
        # self._init_tables()

    def _load_env(self) -> None:
        """
        Load environment variables from .env file.
        This allows storing sensitive connection information as environment variables.
        """
        # Look for .env file in different locations
        env_paths = [
            Path.cwd() / ".env",  # Current working directory
            Path.home() / ".env",  # User's home directory
            Path(__file__).parent / ".env",  # Module directory
            Path(__file__).parents[3] / ".env",  # Project root directory
        ]

        for env_path in env_paths:
            if env_path.exists():
                load_dotenv(dotenv_path=env_path)
                logger.info(f"Loaded environment variables from {env_path}")
                return

        logger.info("No .env file found, using existing environment variables")

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
        """
        Initialize tables in ADX if they don't exist.
        This is optional and depends on configuration.
        """
        for table_name, columns in self.tables.items():
            try:
                # Check if table exists
                query = f".show table {table_name} schema"
                result = self.kusto_client.execute(self.database_name, query)

                # If we get here, table exists
                logger.info(
                    f"Table {table_name} already exists in database {self.database_name}"
                )
                continue
            except KustoServiceError:
                # If exception, table doesn't exist, create it
                logger.info(
                    f"Creating table {table_name} in database {self.database_name}"
                )

                # Build column definitions
                column_defs = []
                for col in columns:
                    col_name = col["name"]
                    # Convert SQL types to Kusto types
                    col_type = self._map_to_kusto_type(col["type"])
                    column_defs.append(f"['{col_name}']:{col_type}")

                # Create the table
                create_table_command = (
                    f".create table {table_name} ({', '.join(column_defs)})"
                )
                try:
                    self.kusto_client.execute_mgmt(
                        self.database_name, create_table_command
                    )
                    logger.info(f"Successfully created table {table_name}")
                except KustoServiceError as e:
                    logger.error(f"Failed to create table {table_name}: {e}")
                    raise

    def _map_to_kusto_type(self, sql_type: str) -> str:
        """
        Maps SQL-like type strings to Kusto data types.

        Args:
            sql_type: SQL-style type string from config

        Returns:
            Kusto type string
        """
        sql_type = sql_type.upper()

        if sql_type.startswith(("TEXT", "VARCHAR", "CHAR")):
            return "string"
        elif sql_type.startswith(("INTEGER", "SMALLINT", "INT")):
            return "int"
        elif sql_type.startswith(("BIGINT")):
            return "long"
        elif sql_type.startswith(("REAL", "NUMERIC", "DECIMAL", "DOUBLE")):
            return "real"
        elif sql_type.startswith(("FLOAT")):
            return "real"
        elif sql_type.startswith(("BOOLEAN", "BOOL")):
            return "bool"
        elif sql_type.startswith(("TIMESTAMP", "DATETIME")):
            return "datetime"
        elif sql_type.startswith("DATE"):
            return "date"
        elif sql_type.startswith("TIME"):
            return "timespan"
        elif sql_type.startswith(("BLOB", "BINARY", "BYTEA")):
            return "dynamic"
        elif sql_type.startswith(("JSON", "JSONB")):
            return "dynamic"
        else:
            logger.warning(f"Unknown SQL type: {sql_type}, defaulting to 'string'")
            return "string"

    def _kusto_type_check(self, value: Any, col_type: str) -> bool:
        """
        Check if value matches expected Kusto type

        Args:
            value: The value to check
            col_type: SQL-style type from config

        Returns:
            True if type is compatible, False otherwise
        """
        kusto_type = self._map_to_kusto_type(col_type)

        if value is None:
            return True  # NULL values allowed for any type

        if kusto_type == "string":
            return isinstance(value, str)
        elif kusto_type == "int":
            return isinstance(value, int) and -2147483648 <= value <= 2147483647
        elif kusto_type == "long":
            return isinstance(value, int)
        elif kusto_type == "real":
            return isinstance(value, (int, float))
        elif kusto_type == "bool":
            return isinstance(value, bool)
        elif kusto_type in ("datetime", "date"):
            return isinstance(value, (datetime, str))
        elif kusto_type == "timespan":
            return isinstance(value, (timedelta, str))
        elif kusto_type == "dynamic":
            return True  # Dynamic can hold any type
        else:
            return True  # Unknown type, assume it's valid

    def output(self, name: str, *args, **kwargs) -> None:
        """
        Output data to ADX cluster using a standardized schema

        Args:
            name: Table name to insert data
            site: Site identifier (optional, defaults to config value)
            **kwargs: Data to be inserted as JSON in the 'data' field

        Returns:
            None
        """
        # Only prints the first 10 characters of the args and kwargs for brevity
        # if kwargs:
            # logger.warning(f"ADX output called for table '{name}' with kwargs: {kwargs[:10]}")
        # Append the kwargs to a file
        # with open("output.txt", "a") as f:
            # f.write(f"Table: {name}, Args: {args}, Kwargs: {kwargs}\n")

        if name not in self.tables:
            logger.error(f"Table '{name}' not defined in the configuration")
            raise ValueError(f"Table '{name}' not defined in the configuration")

        # Get site from kwargs or from config
        site = kwargs.pop("site", self.config.get("default_site", "unknown"))
        logger.debug(f"Using site identifier: {site}")

        # Create a UTC timestamp for when the data is being sent
        date_time_generated = datetime.now(timezone.utc)
        logger.debug(f"Using timestamp: {date_time_generated.isoformat()}")

        # Convert kwargs to JSON string and then to base64
        # kwargs_json = json.dumps(kwargs)

        # TODO: Testing compression
        # logger.info(f"before compressed: {sys.getsizeof(kwargs_json)}")
        # x = zlib.compress(kwargs_json.encode('utf-8'))
        # base64_x = base64.b64encode(x).decode('utf-8')
        # logger.info(f"after compressed: {sys.getsizeof(x)}")
        # End of testing

        # base64_data = base64.b64encode(kwargs_json.encode('utf-8')).decode('utf-8')
        # total_length = len(base64_data)
        
        # Generate a single correlation ID for all payload parts
        # correlation_id = str(uuid4())

        # Calculate the size of each part (roughly equal halves)
        # part_size = (total_length + 1) // 2  # Ceiling division
        
        # Split the base64 string into 2 parts
        # parts = []
        # for i in range(0, 2):
        #     start_idx = i * part_size
        #     end_idx = min((i + 1) * part_size, total_length)

            # If this is the last part that has content
            # if start_idx >= total_length:
            #     parts.append("")
            # else:
            #     parts.append(base64_data[start_idx:end_idx])

        # logger.debug(f"Split base64 encoded data of length {total_length} into 2 parts with correlation ID: {correlation_id}")
        
        # Create payloads for each part
        # payloads = []
        # for i, part in enumerate(parts):
        #     payload = {
        #         "dateTimeGenerated": date_time_generated.isoformat(),
        #         "site": site,
        #         "data": part,  # JSON string part instead of dictionary
        #         "correlationId": correlation_id,
        #         "partIndex": i,
        #         "totalParts": len(parts),
        #     }
        #     payloads.append(payload)
        #     logger.debug(f"Part {i+1} size: {len(part)} characters")

        # Create individual payload
        payloads = [
            {
                "site": site,
                "dateTimeGenerated": date_time_generated.isoformat(),
                "data": kwargs,
            }
        ]

        try:
            # Create a pandas DataFrame with all payloads
            df = pd.DataFrame(payloads)
            logger.debug(f"Created DataFrame with schema: {df.dtypes}")
        except ImportError:
            logger.error("pandas is required for ADX ingestion")
            raise ImportError("pandas is required for ADX ingestion")
        except Exception as e:
            logger.error(f"Failed to create DataFrame: {e}")
            raise

        logger.info(f"database_name: {self.database_name}")

        # Set up ingestion properties with proper mapping
        ingestion_props = IngestionProperties(
            database=self.database_name,
            table=name,
            data_format=DataFormat.JSON,
            ingestion_mapping_reference="json_mapping",
            ingestion_mapping_kind=IngestionMappingKind.JSON,
            report_level=ReportLevel.FailuresAndSuccesses,  # Get detailed reporting
            report_method=ReportMethod.Queue,  # Report via the queue
        )

        logger.debug(
            f"Ingestion properties set for database: {self.database_name}, table: {name}"
        )

        try:
            logger.info(f"the dataframe: {df}")

            self.ingest_client.ingest_from_dataframe(
                df, ingestion_properties=ingestion_props
            )

            logger.info(f"Successfully queued data for ingestion to table {name}")
        except Exception as e:
            logger.error(f"Failed to ingest data to ADX table {name}: {e}")
            raise

    def start_status_monitoring(self) -> None:
        """
        Start a background thread to monitor and print ingestion status.
        This monitors both success and failure queues.
        """
        if self.status_monitor is not None and self.status_monitor.is_alive():
            logger.warning("Status monitoring thread is already running")
            return

        # Reset the stop event flag
        self.monitor_stop_event.clear()

        # Create and start the status monitoring thread
        self.status_monitor = threading.Thread(
            target=self._status_monitoring_worker,
            daemon=True,  # This ensures the thread exits when the main program exits
            name="adx-status-monitor",
        )

        logger.info("Starting ADX ingestion status monitoring thread")
        self.status_monitor.start()
        logger.debug("ADX ingestion status monitoring thread started")

    def stop_status_monitoring(self) -> None:
        """
        Stop the status monitoring thread if it's running.
        """
        if self.status_monitor is None or not self.status_monitor.is_alive():
            logger.warning("Status monitoring thread is not running")
            return

        logger.info("Stopping ADX ingestion status monitoring thread")
        # Signal the thread to stop
        self.monitor_stop_event.set()

        # Wait for the thread to finish with a timeout
        self.status_monitor.join(timeout=5.0)

        if self.status_monitor.is_alive():
            logger.warning(
                "Status monitoring thread did not stop gracefully within timeout"
            )
        else:
            logger.info("ADX ingestion status monitoring thread stopped")
            self.status_monitor = None

    def _status_monitoring_worker(self) -> None:
        """
        Worker function for the status monitoring thread.
        Checks status queues and prints/logs results periodically.
        Based on the sample code: https://github.com/Azure/azure-kusto-python/blob/master/azure-kusto-ingest/tests/sample.py
        """
        logger.info("Status monitoring worker thread started")

        try:
            # Create the status queues client
            status_queues = KustoIngestStatusQueues(self.ingest_client)

            # Variables for exponential backoff
            MAX_BACKOFF = 180  # Maximum backoff time in seconds
            backoff = 1  # Initial backoff time in seconds

            # Main monitoring loop
            while not self.monitor_stop_event.is_set():
                # Check if both queues are empty
                if (
                    status_queues.success.is_empty()
                    and status_queues.failure.is_empty()
                ):
                    # Use event with timeout to allow for graceful shutdown
                    if self.monitor_stop_event.wait(timeout=backoff):
                        break  # Exit loop if stop event is set

                    # Increase backoff time for next iteration (exponential backoff)
                    backoff = min(backoff * 2, MAX_BACKOFF)
                    logger.debug(
                        f"No new ingestion status messages. Backing off for {backoff} seconds"
                    )
                    continue

                # Reset backoff if messages were found
                backoff = 1

                # Process success messages
                success_messages = status_queues.success.pop(10)
                if success_messages:
                    logger.info(
                        f"Received {len(success_messages)} success status messages"
                    )
                    for msg in success_messages:
                        logger.info(f"SUCCESS: {msg}")

                # Process failure messages
                failure_messages = status_queues.failure.pop(10)
                if failure_messages:
                    logger.error(
                        f"Received {len(failure_messages)} failure status messages"
                    )
                    for msg in failure_messages:
                        logger.error(f"FAILURE: {msg}")

        except Exception as e:
            logger.error(f"Error in status monitoring thread: {e}", exc_info=True)

        finally:
            logger.info("Status monitoring worker thread exiting")

    def close(self) -> None:
        """
        Close connections and clean up resources
        """
        # Stop the status monitoring thread if it's running
        if self.status_monitor is not None and self.status_monitor.is_alive():
            self.stop_status_monitoring()

        # Nothing specific needed for Kusto clients as they don't have a close method
        logger.info("ADX connections released")
