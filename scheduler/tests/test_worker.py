# -*- coding: utf-8 -*-
"""
對 scheduler.worker 模組的單元測試
"""

import unittest
import time
from multiprocessing import Queue
from scheduler.worker import Worker

class TestWorker(unittest.TestCase):

    def setUp(self):
        """
        在每個測試前執行，設定乾淨的佇列。
        """
        self.task_queue = Queue()
        self.log_queue = Queue()
        # 我們需要將模組中的全域佇列替換為我們的測試佇列
        from unittest import mock
        self.patcher_task = mock.patch('scheduler.worker.task_queue', self.task_queue)
        self.patcher_log = mock.patch('scheduler.worker.log_queue', self.log_queue)
        self.patcher_task.start()
        self.patcher_log.start()

    def tearDown(self):
        """
        在每個測試後執行，停止 patch。
        """
        self.patcher_task.stop()
        self.patcher_log.stop()

    def test_successful_task(self):
        """
        測試：工作者是否能成功執行任務並記錄效能。
        """
        # 1. 準備
        worker = Worker(worker_id=1)
        worker.daemon = True
        task = {'action': 'success_test', 'name': 'GoodJob', 'duration': 0.1}

        # 2. 執行
        self.task_queue.put(task)
        self.task_queue.put(None) # 結束信號
        worker.start()
        worker.join(timeout=5) # 等待工作者結束

        # 3. 驗證
        self.assertFalse(worker.is_alive(), "工作者行程應已結束")
        self.assertFalse(self.log_queue.empty(), "日誌佇列不應為空")

        log_entry = self.log_queue.get()
        self.assertEqual(log_entry['type'], 'performance')
        self.assertEqual(log_entry['worker_id'], 1)
        self.assertEqual(log_entry['task_name'], 'GoodJob')
        self.assertGreater(log_entry['duration_seconds'], 0)
        self.assertTrue(self.log_queue.empty(), "日誌佇列應只有一個項目")

    def test_failed_task(self):
        """
        測試：工作者是否能處理失敗的任務並記錄錯誤。
        """
        # 1. 準備
        worker = Worker(worker_id=2)
        worker.daemon = True
        task = {'action': 'failure_test', 'name': 'BadJob'}

        # 2. 執行
        self.task_queue.put(task)
        self.task_queue.put(None) # 結束信號
        worker.start()
        worker.join(timeout=5)

        # 3. 驗證
        self.assertFalse(worker.is_alive(), "工作者行程應已結束")
        self.assertFalse(self.log_queue.empty(), "日誌佇列不應為空")

        log_entry = self.log_queue.get()
        self.assertEqual(log_entry['type'], 'error')
        self.assertEqual(log_entry['worker_id'], 2)
        self.assertEqual(log_entry['task_name'], 'BadJob')
        self.assertIn("這是一個模擬的任務失敗", log_entry['error_message'])
        self.assertIn("Traceback", log_entry['traceback_details'])
        self.assertTrue(self.log_queue.empty(), "日誌佇列應只有一個項目")

    def test_process_isolation(self):
        """
        測試：一個崩潰的工作者不應影響主行程。
        """
        # 1. 準備
        worker = Worker(worker_id=3)
        worker.daemon = True
        # 這個任務會引發一個未被 _perform_task 內部 try...except 捕獲的錯誤
        # 但會被 run() 方法的頂層 try...except 捕獲
        task = {'action': 'unexpected_error'}

        # 2. 執行
        try:
            self.task_queue.put(task)
            self.task_queue.put(None)
            worker.start()
            worker.join(timeout=5)
        except Exception as e:
            self.fail(f"主測試行程不應因工作者崩潰而引發異常: {e}")

        # 3. 驗證
        self.assertFalse(worker.is_alive())
        log_entry = self.log_queue.get()
        self.assertEqual(log_entry['type'], 'error')
        self.assertEqual(log_entry['worker_id'], 3)

if __name__ == '__main__':
    unittest.main()
