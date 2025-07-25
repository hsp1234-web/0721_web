import asyncio
import psutil
from datetime import datetime
from zoneinfo import ZoneInfo

# 建立一個全域的、可被應用內其他模組存取的 asyncio.Queue
# 這將是所有系統事件的中央訊息中樞。
SYSTEM_EVENTS_QUEUE = asyncio.Queue()

class PerformanceMonitor:
    """
    一個獨立的監控器，定期收集系統性能數據，
    並將其放入中央的 SYSTEM_EVENTS_QUEUE 中。
    """
    def __init__(self, refresh_interval: float = 1.0):
        self.refresh_interval = max(0.5, refresh_interval)
        self._is_running = False
        self._task: asyncio.Task | None = None

    async def _monitor_loop(self):
        """監控迴圈，定期收集數據並放入佇列。"""
        while self._is_running:
            try:
                cpu_percent = psutil.cpu_percent()
                virtual_memory = psutil.virtual_memory()
                ram_percent = virtual_memory.percent

                # 將數據打包成一個標準格式的字典
                stats_payload = {
                    "type": "PERFORMANCE_UPDATE",
                    "timestamp": datetime.now(ZoneInfo("Asia/Taipei")).isoformat(),
                    "data": {
                        "cpu": cpu_percent,
                        "ram": ram_percent,
                    }
                }
                # 將數據放入中央佇列
                await SYSTEM_EVENTS_QUEUE.put(stats_payload)

            except psutil.NoSuchProcess:
                # 當程序退出時，psutil 可能會引發此錯誤
                print("Monitor: Process not found, shutting down monitoring.")
                self._is_running = False
            except Exception as e:
                print(f"Error in performance monitor: {e}")

            await asyncio.sleep(self.refresh_interval)

    def start(self):
        """啟動背景監控任務。"""
        if not self._is_running:
            print(f"Starting performance monitor with {self.refresh_interval}s interval.")
            self._is_running = True
            self._task = asyncio.create_task(self._monitor_loop())

    async def stop(self):
        """停止背景監控任務。"""
        if self._is_running and self._task:
            print("Stopping performance monitor...")
            self._is_running = False
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass  # 任務被取消是正常的
            print("Performance monitor stopped.")

# 使用範例 (如果直接執行此檔案):
async def main():
    monitor = PerformanceMonitor(refresh_interval=2)
    monitor.start()

    try:
        # 從佇列中讀取數據並印出
        for _ in range(5):
            item = await SYSTEM_EVENTS_QUEUE.get()
            print(f"Received from queue: {item}")
            SYSTEM_EVENTS_QUEUE.task_done()
    finally:
        await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main())
