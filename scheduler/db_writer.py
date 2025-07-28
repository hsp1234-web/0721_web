# -*- coding: utf-8 -*-
"""
資料庫寫入器 (Database Writer) 模組

定義了 DatabaseWriter 類別，它在一個單獨的執行緒中運行，
專門負責從日誌佇列中獲取數據並將其安全地寫入 SQLite 資料庫。
"""

import threading
import queue
from .database import get_db_connection

class DatabaseWriter(threading.Thread):
    """
    一個專門用於將日誌寫入資料庫的執行緒。
    """
    def __init__(self, db_path, log_queue):
        super().__init__()
        self.db_path = db_path
        self.log_queue = log_queue
        self.daemon = True  # 設定為守護執行緒，主程式退出時它也會退出
        self._stop_event = threading.Event()

    def run(self):
        """
        執行緒的主迴圈，持續從佇列獲取日誌並寫入資料庫。
        """
        print("[DatabaseWriter] 啟動，開始監聽日誌。")
        con = get_db_connection(self.db_path)
        if not con:
            print("[DatabaseWriter] 無法連接到資料庫，執行緒即將停止。")
            return

        while not self._stop_event.is_set():
            try:
                # 使用 timeout，這樣迴圈可以定期檢查 _stop_event
                log_entry = self.log_queue.get(timeout=1.0)
                if log_entry is None: # 另一種停止方式
                    continue

                self._write_log_entry(con, log_entry)

            except queue.Empty:
                # 佇列為空是正常情況，繼續等待
                continue
            except Exception as e:
                # 在寫入時發生任何錯誤，印出到控制台
                print(f"[DatabaseWriter] 寫入日誌時發生錯誤: {e}")

        con.close()
        print("[DatabaseWriter] 已停止。")

    def _write_log_entry(self, con, log_entry):
        """
        根據日誌類型，將條目寫入對應的資料表。
        """
        cur = con.cursor()
        entry_type = log_entry.pop('type', None)

        if entry_type == 'performance':
            sql = '''INSERT INTO performance_metrics (timestamp, worker_id, task_name, duration_seconds, cpu_usage_percent, memory_usage_mb)
                     VALUES (:timestamp, :worker_id, :task_name, :duration_seconds, :cpu_usage_percent, :memory_usage_mb)'''
        elif entry_type == 'error':
            sql = '''INSERT INTO error_reports (timestamp, worker_id, task_name, error_message, traceback_details)
                     VALUES (:timestamp, :worker_id, :task_name, :error_message, :traceback_details)'''
        elif entry_type == 'log':
            sql = '''INSERT INTO execution_log (timestamp, worker_id, task_name, log_level, message)
                     VALUES (:timestamp, :worker_id, :task_name, :log_level, :message)'''
        else:
            print(f"[DatabaseWriter] 收到未知的日誌類型: {entry_type}")
            return

        try:
            cur.execute(sql, log_entry)
            con.commit()
        except Exception as e:
            print(f"[DatabaseWriter] 執行 SQL 時出錯: {e}")
            con.rollback()

    def stop(self):
        """
        設定停止事件，以優雅地關閉執行緒。
        """
        print("[DatabaseWriter] 收到停止信號...")
        self._stop_event.set()
