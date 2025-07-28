# -*- coding: utf-8 -*-
"""
工作者 (Worker) 模組

定義了 Worker 類別，它繼承自 multiprocessing.Process，
負責從任務佇列中獲取並執行任務。
"""

import multiprocessing
import time
import traceback
from datetime import datetime
import psutil
from .task_queue import task_queue
from .log_queue import log_queue

class Worker(multiprocessing.Process):
    """
    一個獨立的工作者行程，負責執行耗時的任務。
    """
    def __init__(self, worker_id):
        super().__init__()
        self.worker_id = worker_id
        self.name = f"Worker-{worker_id}"

    def run(self):
        """
        工作者的主迴圈，不斷從佇列中獲取任務並執行。
        """
        print(f"[{self.name}] 啟動並開始監聽任務。")
        while True:
            try:
                task = task_queue.get()
                if task is None:  # 收到結束信號
                    print(f"[{self.name}] 收到結束信號，正在關閉。")
                    break

                print(f"[{self.name}] 獲取到任務：{task}")
                self._perform_task(task)

            except Exception as e:
                # 捕獲所有未預期的錯誤，記錄後繼續執行
                error_report = self._create_error_report(task, e)
                log_queue.put(error_report)
                print(f"[{self.name}] 處理任務時發生錯誤，已記錄。")

        print(f"[{self.name}] 已停止。")

    def _perform_task(self, task):
        """
        執行具體的任務，並記錄效能。
        """
        start_time = time.time()
        process = psutil.Process(self.pid)

        try:
            # --- 任務執行邏輯 ---
            action = task.get('action')
            if action == 'success_test':
                print(f"[{self.name}] 正在執行一個成功的測試任務...")
                time.sleep(task.get('duration', 2))
                print(f"[{self.name}] 成功任務完成。")
            elif action == 'failure_test':
                print(f"[{self.name}] 正在執行一個會失敗的測試任務...")
                raise ValueError("這是一個模擬的任務失敗。")
            else:
                raise TypeError(f"未知的任務類型：{action}")

            # --- 效能記錄 ---
            end_time = time.time()
            duration = end_time - start_time
            cpu_usage = process.cpu_percent()
            mem_usage = process.memory_info().rss / (1024 * 1024)  # MB

            performance_data = {
                'type': 'performance',
                'timestamp': datetime.now(),
                'worker_id': self.worker_id,
                'task_name': task.get('name', 'N/A'),
                'duration_seconds': duration,
                'cpu_usage_percent': cpu_usage,
                'memory_usage_mb': mem_usage
            }
            log_queue.put(performance_data)

        except Exception as e:
            # 捕獲任務執行中的具體錯誤
            error_report = self._create_error_report(task, e)
            log_queue.put(error_report)
            print(f"[{self.name}] 任務 '{task.get('name')}' 執行失敗。")

    def _create_error_report(self, task, e):
        """
        建立標準化的錯誤報告。
        """
        return {
            'type': 'error',
            'timestamp': datetime.now(),
            'worker_id': self.worker_id,
            'task_name': task.get('name', 'N/A'),
            'error_message': str(e),
            'traceback_details': traceback.format_exc()
        }
