# -*- coding: utf-8 -*-
import threading
import sqlite3
import time
from pathlib import Path
import psutil

class DatabaseLogger:
    """
    獨立的資料庫記錄器，在背景執行緒中運行，
    負責將所有日誌和硬體數據高頻寫入 SQLite 資料庫。
    """
    def __init__(self, db_path: Path, log_manager):
        self._db_path = db_path
        self._log_manager = log_manager
        self._stop_event = threading.Event()
        self._db_thread = threading.Thread(target=self._run)
        self._processed_log_timestamps = set()

    def _setup_database(self):
        """初始化資料庫和資料表"""
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            # 硬體數據表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS hardware_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                cpu_percent REAL,
                ram_percent REAL
            )
            """)
            # 事件日誌表
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS event_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                level TEXT,
                message TEXT
            )
            """)
            conn.commit()

    def _run(self):
        """背景執行緒的核心循環"""
        self._setup_database()

        while not self._stop_event.is_set():
            conn = sqlite3.connect(self._db_path, timeout=10)
            cursor = conn.cursor()

            # 1. 記錄硬體數據
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            ts = self._log_manager.get_taipei_time()
            cursor.execute(
                "INSERT INTO hardware_log (timestamp, cpu_percent, ram_percent) VALUES (?, ?, ?)",
                (ts, cpu, ram)
            )

            # 2. 記錄新的日誌事件
            recent_logs = self._log_manager.get_recent_logs(count=100) # 獲取足夠多的日誌以防遺漏
            for log in recent_logs:
                # 使用時間戳作為唯一標識，避免重複寫入
                if log['timestamp'] not in self._processed_log_timestamps:
                    cursor.execute(
                        "INSERT INTO event_log (timestamp, level, message) VALUES (?, ?, ?)",
                        (log['timestamp'], log['level'], log['message'])
                    )
                    self._processed_log_timestamps.add(log['timestamp'])

            conn.commit()
            conn.close()

            # 控制寫入頻率
            time.sleep(1) # 每秒寫入一次資料庫

    def start(self):
        """啟動資料庫記錄執行緒"""
        self._stop_event.clear()
        self._db_thread.start()
        print("資料庫記錄器已啟動。")

    def stop(self):
        """停止資料庫記錄執行緒"""
        self._stop_event.set()
        self._db_thread.join(timeout=5) # 等待執行緒結束
        print("資料庫記錄器已停止。")
