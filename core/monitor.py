# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   核心檔案：core/monitor.py (v2.0 升級版)                          ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       硬體資源的「情報員」。它在背景獨立運作，持續偵測 CPU 與       ║
# ║       RAM 的使用率。                                                 ║
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       職責單一，只負責收集數據。它不再直接輸出到畫面，而是將格式      ║
# ║       化後的硬體狀態字串，以高頻率「匯報」給視覺指揮官              ║
# ║       (PresentationManager)，由其統一更新到畫面的即時狀態層。      ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

import threading
import time
import psutil
from datetime import datetime

class HardwareMonitor:
    """
    在背景執行緒中監控 CPU 和 RAM 使用率。
    """
    def __init__(self, presentation_manager, interval=1.0):
        """
        初始化監控器。
        :param presentation_manager: 視覺指揮官的實例。
        :param interval: 更新間隔（秒）。
        """
        self.pm = presentation_manager
        self.interval = interval
        self.is_running = False
        self._thread = None

    def _monitor(self):
        """
        監控迴圈，會在新執行緒中執行。
        """
        self.is_running = True
        while self.is_running:
            try:
                # 獲取硬體資訊
                cpu_percent = psutil.cpu_percent()
                ram_percent = psutil.virtual_memory().percent
                timestamp = datetime.now().strftime('%H:%M:%S')

                # 格式化字串
                hardware_string = f"[{timestamp}] CPU: {cpu_percent:5.1f}% | RAM: {ram_percent:5.1f}%"

                # 將情報匯報給視覺指揮官
                self.pm.update_hardware_status(hardware_string)

                # 等待下一個週期
                time.sleep(self.interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # 在某些情況下，程序可能已經結束，這時會拋出異常
                self.pm.update_hardware_status("硬體監控：程序結束")
                break
            except Exception:
                # 捕獲其他潛在錯誤
                self.pm.update_hardware_status("硬體監控：發生錯誤")
                break

    def start(self):
        """
        啟動背景監控執行緒。
        """
        if not self.is_running:
            self._thread = threading.Thread(target=self._monitor, daemon=True)
            self._thread.start()

    def stop(self):
        """
        停止監控。
        """
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval * 2) # 等待執行緒結束

