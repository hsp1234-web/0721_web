# integrated_platform/src/display_manager.py

import threading
import time
import sqlite3
from pathlib import Path
from IPython.display import display, clear_output
import ipywidgets as widgets

class DisplayManager:
    """
    職責：作為唯一的「畫家」，從 SQLite 讀取日誌並在 Colab 中穩定地顯示。
    """
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.last_log_id = 0

        # --- UI 元件 ---
        self.log_output = widgets.Output(layout={'border': '1px solid black', 'height': '300px', 'overflow_y': 'scroll'})
        self.status_label = widgets.Label(value="狀態：正在初始化...")
        self.ui = widgets.VBox([self.status_label, self.log_output])

    def _get_connection(self):
        """返回一個新的資料庫連接。"""
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _fetch_new_logs(self):
        """從資料庫中獲取新的日誌。"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT id, timestamp, level, message FROM logs WHERE id > ? ORDER BY id ASC",
                    (self.last_log_id,)
                )
                logs = cursor.fetchall()
                if logs:
                    self.last_log_id = logs[-1][0]
                return logs
        except sqlite3.Error:
            # 如果資料庫尚未建立或表格不存在，則返回空列表
            return []

    def _run(self):
        """背景執行緒的主循環，定期刷新顯示。"""
        while not self.stop_event.is_set():
            logs = self._fetch_new_logs()
            if logs:
                with self.log_output:
                    for log_id, timestamp, level, message in logs:
                        print(f"[{timestamp}] [{level}] {message}")

            # 更新狀態（這裡可以擴展為更複雜的邏輯）
            self.status_label.value = f"狀態：運行中... (最後檢查時間: {time.strftime('%H:%M:%S')})"

            time.sleep(1) # 每秒輪詢一次

    def start(self):
        """啟動顯示管理器並顯示 UI。"""
        display(self.ui)
        self.thread.start()

    def stop(self):
        """停止背景執行緒。"""
        self.stop_event.set()
        self.thread.join()
        self.status_label.value = "狀態：已停止。"
        with self.log_output:
            print("--- 日誌顯示結束 ---")
