# log_manager.py

import sqlite3
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

class LogManager:
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self._create_table()

    def _create_table(self):
        CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL
        );
        """
        with self.conn:
            self.conn.execute(CREATE_TABLE_SQL)

    def log(self, level: str, message: str):
        timestamp = datetime.datetime.now(ZoneInfo("Asia/Taipei")).isoformat()
        INSERT_LOG_SQL = """
        INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?);
        """
        with self.conn:
            self.conn.execute(INSERT_LOG_SQL, (timestamp, level, message))

    def close(self):
        if self.conn:
            self.conn.close()
