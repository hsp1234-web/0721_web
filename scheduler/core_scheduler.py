# -*- coding: utf-8 -*-
"""
核心調度器 (Core Scheduler) 模組

定義了 Scheduler 類別，它是整個任務調度服務的大腦。
負責啟動、管理和關閉工作者行程以及資料庫寫入器。
"""

import time
import os
import psutil
from .worker import Worker
from .db_writer import DatabaseWriter
from .task_queue import task_queue
from .log_queue import log_queue
from .database import initialize_database, get_db_connection

class Scheduler:
    """
    核心調度器，管理整個服務的生命週期。
    """
    def __init__(self, db_path, num_workers=None):
        self.db_path = db_path
        if num_workers is None:
            self.num_workers = os.cpu_count() or 1
        else:
            self.num_workers = num_workers

        self.worker_pool = []
        self.db_writer = None
        self.db_connection = None
        self._monitor_thread = None
        self._stop_event = False

    def start(self):
        """
        啟動整個調度服務。
        """
        print("[Scheduler] 正在啟動...")

        # 1. 確保資料庫和資料表存在
        initialize_database(self.db_path)

        # 2. 啟動資料庫寫入器，讓它自己管理連接
        self.db_writer = DatabaseWriter(self.db_path, log_queue)
        self.db_writer.start()

        # 3. 啟動工作者行程池
        print(f"[Scheduler] 正在啟動 {self.num_workers} 個工作者...")
        for i in range(self.num_workers):
            worker = Worker(worker_id=i+1)
            self.worker_pool.append(worker)
            worker.start()

        print("[Scheduler] 啟動完成。")

    def add_task(self, task):
        """
        向任務佇列中添加一個新任務。
        """
        task_queue.put(task)
        print(f"[Scheduler] 已添加任務：{task.get('name', 'N/A')}")

    def shutdown(self):
        """
        優雅地關閉整個服務。
        """
        print("[Scheduler] 正在關閉...")

        # 1. 停止向佇列中添加新任務 (由應用邏輯保證)

        # 2. 向工作者發送結束信號
        for _ in self.worker_pool:
            task_queue.put(None)

        # 3. 等待所有工作者行程結束
        for worker in self.worker_pool:
            worker.join()
        print("[Scheduler] 所有工作者已停止。")

        # 4. 等待日誌佇列處理完畢
        while not log_queue.empty():
            print("[Scheduler] 等待日誌佇列清空...")
            time.sleep(1)

        # 5. 停止資料庫寫入器
        if self.db_writer:
            self.db_writer.stop()
            self.db_writer.join()
        print("[Scheduler] 資料庫寫入器已停止。")

        # 6. 資料庫連接由 db_writer 自行關閉

        print("[Scheduler] 關閉完成。")

    def _monitor_resources(self):
        """
        (暫未啟用) 監控系統資源的執行緒函式。
        """
        while not self._stop_event:
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_info = psutil.virtual_memory()
            print(f"[Monitor] CPU 使用率: {cpu_usage}%, 可用記憶體: {memory_info.available / (1024*1024):.2f} MB")
            time.sleep(5)
