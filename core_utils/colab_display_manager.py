# -*- coding: utf-8 -*-
import threading
import time
from IPython.display import display, clear_output
import psutil

class ColabDisplayManager:
    def __init__(self, stats, log_manager):
        self._stats = stats
        self._log_manager = log_manager
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _get_hardware_usage(self):
        return f"CPU: {psutil.cpu_percent()}% | RAM: {psutil.virtual_memory().percent}%"

    def _run(self):
        start_time = time.time()
        while not self._stop_event.is_set():
            try:
                clear_output(wait=True)

                # 儀表板標題
                print("╔══════════════════════════════════════════════════════════════════╗")
                print("║                    🚀 Colab 動態執行儀表板 🚀                    ║")
                print("╚══════════════════════════════════════════════════════════════════╝")

                # 硬體和時間
                elapsed_time = time.time() - start_time
                print(f"⏱️ 執行時間: {elapsed_time:.2f}s | 💻 硬體資源: {self._get_hardware_usage()}")
                print("-" * 70)

                # 當前任務
                print(f"🎯 當前任務: {self._stats.get('current_task', '初始化中...')}")
                print("-" * 70)

                # 狀態區塊
                print("🚦 系統狀態:")
                print(f"  - Git 倉庫: {self._stats.get('repo_status', '⚪ 等待中...')}")
                print(f"  - 核心依賴: {self._stats.get('deps_status', '⚪ 等待中...')}")
                print(f"  - E2E 測試: {self._stats.get('test_status', '⚪ 等待中...')}")
                print(f"  - 後端服務: {self._stats.get('service_status', '⚪ 等待中...')}")
                print("-" * 70)

                # 日誌區塊
                print("📜 即時日誌:")
                logs = self._log_manager.get_recent_logs(10)
                for log_entry in logs:
                    print(f"  {log_entry}")

                time.sleep(0.25) # 刷新率
            except Exception as e:
                # 在 Colab 中，clear_output 有時會因各種原因失敗，這裡做個保護
                print(f"DisplayManager 發生錯誤: {e}")
                time.sleep(1)


    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join(timeout=1)
        # 最終再渲染一次，確保顯示最終狀態
        try:
            clear_output(wait=True)
            print("╔══════════════════════════════════════════════════════════════════╗")
            print("║                       ✅ 所有任務已完成 ✅                       ║")
            print("╚══════════════════════════════════════════════════════════════════╝")
            print(f"🎯 最終狀態: {self._stats.get('current_task', '已結束')}")
            print("-" * 70)
            print("📜 最終日誌:")
            logs = self._log_manager.get_recent_logs(15)
            for log_entry in logs:
                print(f"  {log_entry}")
        except Exception as e:
            print(f"最終渲染時發生錯誤: {e}")
