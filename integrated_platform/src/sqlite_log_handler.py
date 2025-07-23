# integrated_platform/src/sqlite_log_handler.py
import logging
import sqlite3
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

class SQLiteHandler(logging.Handler):
    """
    一個自訂的 logging handler，可將日誌記錄寫入指定的 SQLite 資料庫。
    這使其能夠與 Colab 的 LogManager 系統無縫整合。
    """
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.lock = threading.Lock()
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _create_table(self):
        with self.lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("""
                    CREATE TABLE IF NOT EXISTS logs (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        level TEXT NOT NULL,
                        message TEXT NOT NULL
                    );
                    """)
                    conn.commit()
            except Exception as e:
                # 在初始化階段，如果出錯，打印到控制台是可接受的
                print(f"CRITICAL DB HANDLER SETUP ERROR: {e}")

    def emit(self, record):
        """
        當 logger 產生一條日誌時，此方法會被呼叫。
        """
        ts = datetime.fromtimestamp(record.created, ZoneInfo("Asia/Taipei")).isoformat()
        msg = self.format(record)
        with self.lock:
            try:
                with self._get_connection() as conn:
                    conn.execute(
                        "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?);",
                        (ts, record.levelname, msg)
                    )
                    conn.commit()
            except Exception as e:
                # 如果在運行時寫入日誌失敗，我們不希望讓整個應用崩潰
                # 而是將錯誤打印到 stderr
                import sys
                sys.stderr.write(f"CRITICAL DB LOGGING ERROR: {e}\n")
