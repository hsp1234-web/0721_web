# -*- coding: utf-8 -*-
"""
對 scheduler.db_writer 模組的單元測試
"""

import unittest
import sqlite3
import time
from multiprocessing import Queue
from datetime import datetime
from scheduler.database import initialize_database
from scheduler.db_writer import DatabaseWriter

class TestDatabaseWriter(unittest.TestCase):

    def setUp(self):
        """
        設定一個記憶體中的 SQLite 資料庫和一個日誌佇列。
        """
        self.db_path = ":memory:"
        # self.con = sqlite3.connect(self.db_path, check_same_thread=False)
        # initialize_database(self.db_path) # 雖然是 memory, 但初始化還是需要路徑

        # 重新連接以在主執行緒中獲得正確的控制代碼
        self.con = sqlite3.connect(self.db_path, check_same_thread=False)
        initialize_database(self.con)

        self.log_queue = Queue()
        self.db_writer = DatabaseWriter(self.con, self.log_queue)
        self.db_writer.start()

    def tearDown(self):
        """
        優雅地停止 DatabaseWriter 執行緒並關閉連接。
        """
        self.db_writer.stop()
        self.db_writer.join(timeout=5)
        self.assertFalse(self.db_writer.is_alive(), "DatabaseWriter 執行緒應已停止")
        self.con.close()

    def test_write_performance_log(self):
        """
        測試：寫入一條效能日誌。
        """
        # 1. 準備
        perf_data = {
            'type': 'performance',
            'timestamp': datetime.now(),
            'worker_id': 1,
            'task_name': 'PerfTask',
            'duration_seconds': 1.23,
            'cpu_usage_percent': 50.5,
            'memory_usage_mb': 100.1
        }

        # 2. 執行
        self.log_queue.put(perf_data)
        time.sleep(1.5) # 給予足夠時間讓 writer 處理

        # 3. 驗證
        cur = self.con.cursor()
        cur.execute("SELECT * FROM performance_metrics")
        rows = cur.fetchall()

        self.assertEqual(len(rows), 1, "應有一條效能紀錄")
        row = rows[0]
        self.assertEqual(row[2], 1) # worker_id
        self.assertEqual(row[3], 'PerfTask') # task_name
        self.assertAlmostEqual(row[6], 100.1, places=1) # memory_usage_mb

    def test_write_error_log(self):
        """
        測試：寫入一條錯誤報告。
        """
        # 1. 準備
        error_data = {
            'type': 'error',
            'timestamp': datetime.now(),
            'worker_id': 2,
            'task_name': 'ErrorTask',
            'error_message': 'Something went wrong',
            'traceback_details': 'Traceback...'
        }

        # 2. 執行
        self.log_queue.put(error_data)
        time.sleep(1.5)

        # 3. 驗證
        cur = self.con.cursor()
        cur.execute("SELECT * FROM error_reports")
        rows = cur.fetchall()

        self.assertEqual(len(rows), 1, "應有一條錯誤報告")
        row = rows[0]
        self.assertEqual(row[2], 2) # worker_id
        self.assertEqual(row[3], 'ErrorTask') # task_name
        self.assertEqual(row[4], 'Something went wrong') # error_message

    def test_write_multiple_logs(self):
        """
        測試：寫入多種類型的日誌。
        """
        # 1. 準備
        perf_data = {
            'type': 'performance', 'timestamp': datetime.now(), 'worker_id': 3,
            'task_name': 'MultiTask1', 'duration_seconds': 2.0, 'cpu_usage_percent': 10.0, 'memory_usage_mb': 20.0
        }
        error_data = {
            'type': 'error', 'timestamp': datetime.now(), 'worker_id': 4,
            'task_name': 'MultiTask2', 'error_message': 'Multi error', 'traceback_details': '...'
        }

        # 2. 執行
        self.log_queue.put(perf_data)
        self.log_queue.put(error_data)
        time.sleep(2)

        # 3. 驗證
        cur = self.con.cursor()
        perf_rows = cur.execute("SELECT * FROM performance_metrics").fetchall()
        error_rows = cur.execute("SELECT * FROM error_reports").fetchall()

        self.assertEqual(len(perf_rows), 1)
        self.assertEqual(len(error_rows), 1)

if __name__ == '__main__':
    unittest.main()
