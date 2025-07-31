# -*- coding: utf-8 -*-
"""
鳳凰之心指揮中心 TUI 核心模組 (V3 架構)
"""
import time
import threading
from collections import deque
from IPython.display import clear_output
import psutil
import datetime

class CommanderConsole:
    """
    管理 Colab 輸出儲存格的 TUI 儀表板。
    使用 clear_output 和 print 實現，專為 V3 指揮中心架構設計。
    """

    def __init__(self, max_log_entries=15):
        """
        初始化儀表板。
        :param max_log_entries: 上半部「近況彙報」區顯示的最大日誌行數。
        """
        self.log_buffer = deque(maxlen=max_log_entries)
        self._lock = threading.Lock()
        self._stop_event = threading.Event()
        self._monitor_thread = None

        # --- 即時狀態行的數據 ---
        self.start_time = time.time()
        self.cpu_usage = 0.0
        self.ram_usage = 0.0
        self.status_tag = "[初始化中...]"

    def _render(self):
        """
        核心渲染函數。
        它會清除目前的輸出，然後重繪整個儀表板。
        """
        with self._lock:
            clear_output(wait=True)

            # --- 1. 繪製上半部：近況彙報 ---
            print("┌────────────────── 鳳凰之心指揮中心 V3 ──────────────────┐")
            print("│ 近況彙報 (最新日誌)                                      │")
            print("├──────────────────────────────────────────────────────────┤")

            # 複製一份緩衝區以避免在迭代時發生變更
            logs_to_render = list(self.log_buffer)
            for i in range(self.log_buffer.maxlen):
                if i < len(logs_to_render):
                    log_line = logs_to_render[i]
                    # 截斷過長的日誌以避免破壞排版
                    if len(log_line) > 56:
                        log_line = log_line[:53] + "..."
                    print(f"│ {log_line.ljust(56)} │")
                else:
                    # 打印空行以保持框架完整
                    print("│                                                          │")

            # --- 2. 繪製下半部：即時狀態 (原地刷新) ---
            # 由於 clear_output 的存在，我們不需要 \r，直接打印即可
            print("└──────────────────────────────────────────────────────────┘")

            elapsed_time = str(datetime.timedelta(seconds=int(time.time() - self.start_time)))
            status_line = (
                f"🕒 {elapsed_time} | "
                f"CPU: {self.cpu_usage:5.1f}% | "
                f"RAM: {self.ram_usage:5.1f}% | "
                f"{self.status_tag}"
            )
            # 打印狀態行，並用 flush=True 確保立即輸出
            print(status_line, end="", flush=True)

    def add_log(self, message: str):
        """
        向日誌緩衝區新增一條日誌，並觸發一次低頻的畫面重繪。
        :param message: 要顯示的日誌訊息。
        """
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        # 格式化日誌，使其包含時間戳
        formatted_message = f"[{timestamp}] {message}"
        self.log_buffer.append(formatted_message)
        self._render()

    def update_status_tag(self, new_tag: str):
        """
        更新狀態標籤 (例如：安裝依賴、執行分析)。
        這會觸發一次畫面重繪。
        :param new_tag: 新的狀態標籤文字。
        """
        self.status_tag = new_tag
        self._render()

    def _resource_monitor_loop(self):
        """
        在背景執行緒中運行的循環，高頻更新資源使用率。
        """
        while not self._stop_event.is_set():
            self.cpu_usage = psutil.cpu_percent()
            self.ram_usage = psutil.virtual_memory().percent

            # 觸發重繪以更新狀態行
            self._render()

            # 更新頻率
            time.sleep(1)

    def start(self):
        """
        啟動儀表板的背景資源監控。
        """
        self.add_log("指揮中心介面已啟動。")
        if not self._monitor_thread:
            self._stop_event.clear()
            self._monitor_thread = threading.Thread(target=self._resource_monitor_loop, daemon=True)
            self._monitor_thread.start()

    def stop(self, final_message="任務完成。"):
        """
        停止儀表板的背景更新，並顯示最終訊息。
        :param final_message: 顯示在狀態標籤中的最終訊息。
        """
        if self._monitor_thread:
            self._stop_event.set()
            # 等待執行緒結束
            self._monitor_thread.join(timeout=1.5)
            self._monitor_thread = None

        self.status_tag = f"[ {final_message} ]"
        self._render()
        print("\n") # 在儀表板下方打印一個新行，讓後續輸出更清晰

if __name__ == '__main__':
    # --- 獨立測試 ---
    print("正在測試 CommanderConsole...")
    console = CommanderConsole()
    console.start()

    try:
        # 模擬日誌和狀態更新
        console.add_log("系統初始化...")
        time.sleep(2)
        console.update_status_tag("[安裝依賴: 1/5 (fastapi)]")
        time.sleep(1.5)
        console.add_log("fastapi 安裝成功。")
        console.update_status_tag("[安裝依賴: 2/5 (uvicorn)]")
        time.sleep(1.5)
        console.add_log("uvicorn 安裝成功。")
        console.update_status_tag("[安裝依賴: 3/5 (psutil)]")
        time.sleep(1.5)
        console.add_log("psutil 安裝成功。")
        console.update_status_tag("[執行分析...]")
        time.sleep(3)
        console.add_log("分析完成。")

    except KeyboardInterrupt:
        print("\n手動中斷測試。")
    finally:
        console.stop("測試結束。")
        print("CommanderConsole 測試完畢。")
