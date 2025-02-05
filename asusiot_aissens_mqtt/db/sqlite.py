import json
import sqlite3
from datetime import datetime

from pydantic.config import JsonValue

from asusiot_aissens_mqtt.db.data_saver_interface import DataSaverInterface


class SqliteDataSaver(DataSaverInterface):
    def __init__(self, db_path: str = "data.db") -> None:
        self.conn = sqlite3.connect(db_path)
        self._init_db()

    def _init_db(self) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sensor_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp REAL,
                name TEXT,
                json_value TEXT
            )
            """
        )
        self.conn.commit()

    def save(self, timestamp: datetime, name: str, json_value: JsonValue) -> None:
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO sensor_data (timestamp, name, json_value) VALUES (?, ?, ?)",
            (timestamp, name, json.dumps(json_value)),
        )
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()
