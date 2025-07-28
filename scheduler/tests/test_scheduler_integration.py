# -*- coding: utf-8 -*-
"""
對 scheduler.core_scheduler 模組的整合測試
"""

import unittest
import time
import os
import sqlite3
from scheduler.core_scheduler import Scheduler

class TestSchedulerIntegration(unittest.TestCase):

    def setUp(self):
        """
        設定測試用的資料庫檔案。
        """
        self.db_path = "test_scheduler.db"
        # 確保在測試開始前刪除舊的資料庫檔案
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        """
        清理測試後產生的資料庫檔案。
        """
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_full_lifecycle(self):
        """
        測試：調度器的完整生命週期。
        啟動 -> 新增任務 -> 關閉 -> 驗證資料庫
        """
        # 1. 準備
        scheduler = Scheduler(db_path=self.db_path, num_workers=2)

        # 2. 啟動
        scheduler.start()

        # 3. 新增任務
        tasks = [
            {'action': 'success_test', 'name': 'Success-1', 'duration': 0.1},
            {'action': 'failure_test', 'name': 'Failure-1'},
            {'action': 'success_test', 'name': 'Success-2', 'duration': 0.2},
            {'action': 'unexpected_error', 'name': 'Unknown-1'}
        ]
        for task in tasks:
            scheduler.add_task(task)

        # 給予足夠的時間讓所有任務被處理
        time.sleep(3)

        # 4. 關閉
        scheduler.shutdown()

        # 5. 驗證
        self.assertFalse(any(p.is_alive() for p in scheduler.worker_pool), "所有工作者行程都應已停止")
        self.assertFalse(scheduler.db_writer.is_alive(), "資料庫寫入器執行緒應已停止")

        con = sqlite3.connect(self.db_path)
        cur = con.cursor()

        # 驗證效能記錄
        cur.execute("SELECT * FROM performance_metrics")
        perf_rows = cur.fetchall()
        self.assertEqual(len(perf_rows), 2, "應有 2 筆成功的效能紀錄")

        # 驗證錯誤報告
        cur.execute("SELECT * FROM error_reports")
        error_rows = cur.fetchall()
        self.assertEqual(len(error_rows), 2, "應有 2 筆失敗的錯誤報告")

        # 抽樣檢查一條錯誤報告
        cur.execute("SELECT * FROM error_reports WHERE task_name = 'Failure-1'")
        failure_task_row = cur.fetchone()
        self.assertIsNotNone(failure_task_row)
        self.assertIn("模擬的任務失敗", failure_task_row[4]) # error_message

        con.close()

if __name__ == '__main__':
    unittest.main()
