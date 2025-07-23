# log_manager.py (草圖)

# --- 導入所需模組 ---
import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

class LogManager:
    """
    職責：管理所有日誌的寫入，並與 SQLite 數據庫互動。
    必須是執行緒安全的，以應對可能的並行寫入。
    """
    def __init__(self, db_path: Path):
        """
        Jules 需實現：
        1. 初始化時，儲存資料庫路徑。
        2. 建立一個執行緒鎖 (threading.Lock) 來保護資料庫寫入。
        3. 呼叫一個內部方法 `_create_table()` 來確保資料庫和表格存在。
        """
        self.db_path = db_path
        self.lock = threading.Lock()
        self._create_table()

    def get_connection(self):
        """返回一個新的資料庫連接。"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _create_table(self):
        """
        在初始化時被呼叫，確保 'logs' 表格存在。
        """
        CREATE_TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL
        );
        """
        try:
            with self.get_connection() as conn:
                conn.execute(CREATE_TABLE_SQL)
        except sqlite3.Error as e:
            # 在真實世界的應用中，這裡應該有更完善的錯誤處理
            print(f"資料庫錯誤: {e}")


    def log(self, level: str, message: str):
        """
        職責：將一條新的日誌記錄安全地寫入數據庫。
        Jules 需實現：
        1. 使用 with self.lock: 來獲取執行緒鎖。
        2. 獲取當前「亞洲/台北」時區的時間。
        3. 使用 .isoformat() 方法將其轉換為 ISO 8601 格式的字串。
        4. 執行以下的 SQL 指令，將時間、等級、訊息插入表格。
        """
        # SQL 指令草圖
        INSERT_LOG_SQL = "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?);"

        with self.lock:
            try:
                # 每次都建立新的連線，確保執行緒安全
                with self.get_connection() as conn:
                    timestamp = datetime.now(ZoneInfo("Asia/Taipei")).isoformat()
                    conn.execute(INSERT_LOG_SQL, (timestamp, level, message))
            except sqlite3.Error as e:
                # 同樣地，這裡應該有更完善的錯誤處理
                print(f"寫入日誌時發生資料庫錯誤: {e}")
