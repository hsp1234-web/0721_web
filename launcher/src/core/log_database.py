# launcher/src/core/log_database.py

import sqlite3
import threading
from pathlib import Path
from datetime import datetime

class LogDatabase:
    """
    負責將日誌訊息儲存到一個輕量級的 SQLite 資料庫中，並管理其大小。
    """
    def __init__(self, db_path: Path, max_size_kb: int = 1024):
        self.db_path = db_path
        self.max_size_bytes = max_size_kb * 1024
        self.conn = None
        self._lock = threading.Lock()
        self._setup()

    def _setup(self):
        """建立資料庫和資料表。"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = self.conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                )
            """)
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"資料庫錯誤: {e}")
            self.conn = None

    def log(self, level: str, message: str):
        """將一條日誌寫入資料庫。"""
        if not self.conn:
            return

        with self._lock:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?)",
                    (datetime.now(), level.upper(), message)
                )
                self.conn.commit()
                self._manage_size()
            except sqlite3.Error as e:
                print(f"寫入日誌到資料庫時出錯: {e}")

    def _manage_size(self):
        """檢查資料庫大小，如果超過上限，則刪除舊的日誌。"""
        try:
            db_size = self.db_path.stat().st_size
            if db_size > self.max_size_bytes:
                # 計算要刪除的日誌數量 (例如，刪除 20% 的舊日誌)
                cursor = self.conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM logs")
                count = cursor.fetchone()[0]
                limit = int(count * 0.2)

                if limit > 0:
                    cursor.execute(f"""
                        DELETE FROM logs WHERE id IN (
                            SELECT id FROM logs ORDER BY timestamp ASC LIMIT {limit}
                        )
                    """)
                    self.conn.commit()
                    # 釋放空間
                    self.conn.execute("VACUUM")
                    self.conn.commit()
        except (sqlite3.Error, FileNotFoundError) as e:
             print(f"管理資料庫大小時出錯: {e}")

    def close(self):
        """關閉資料庫連線。"""
        if self.conn:
            self.conn.close()
