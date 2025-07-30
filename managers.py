# -*- coding: utf-8 -*-
import threading
import time
from collections import deque
import psutil
from IPython.display import display, clear_output
import ipywidgets as widgets
from datetime import datetime
import pytz

class LogManager:
    """中央日誌管理器，負責處理、緩衝和分發日誌訊息"""
    def __init__(self, buffer_size=100):
        self.log_buffer = deque(maxlen=buffer_size)
        self._lock = threading.Lock()
        self.taipei_tz = pytz.timezone("Asia/Taipei")

    def get_taipei_time(self):
        """獲取帶有毫秒和時區的台北時間"""
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        now_taipei = now_utc.astimezone(self.taipei_tz)
        return now_taipei.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] + f" ({self.taipei_tz})"

    def log(self, level, message):
        """記錄一條新的日誌"""
        log_entry = {
            "timestamp": self.get_taipei_time(),
            "level": level.upper(),
            "message": message
        }
        with self._lock:
            self.log_buffer.append(log_entry)

    def get_recent_logs(self, count=10, levels=None):
        """獲取最近的指定數量的日誌"""
        with self._lock:
            if levels:
                levels = [l.upper() for l in levels]
                return [log for log in reversed(self.log_buffer) if log['level'] in levels][:count]
            return list(reversed(self.log_buffer))[:count]

class DisplayManager:
    """顯示管理器，負責在 Colab 中智能地渲染雙區塊儀表板"""
    def __init__(self, log_manager, status_dict):
        self._log_manager = log_manager
        self._status_dict = status_dict
        self._stop_event = threading.Event()
        self._display_thread = threading.Thread(target=self._run_live_indicator)
        self.upper_display_area = widgets.Output()
        self.lower_display_area = widgets.Output()
        self._last_log_count = 0

    def _format_log_message(self, log):
        """格式化單條日誌，並添加顏色"""
        level_colors = {
            "SUCCESS": "color: #34a853;", # 綠色
            "WARNING": "color: #fbbc04;", # 黃色
            "ERROR": "color: #ea4335;",   # 紅色
            "CRITICAL": "color: #ea4335; font-weight: bold;",
            "BATTLE": "color: #4285f4; font-weight: bold;", # 藍色
        }
        style = level_colors.get(log['level'], "color: white;")
        return f"<pre style='margin: 0; white-space: pre-wrap; {style}'>[{log['timestamp']}] [{log['level']}] {log['message']}</pre>"

    def _run_live_indicator(self):
        """獨立執行緒，高頻刷新下半部的即時狀態行"""
        while not self._stop_event.is_set():
            with self.lower_display_area:
                now_time = datetime.now(self._log_manager.taipei_tz).strftime('%H:%M:%S')
                cpu = self._status_dict.get('cpu', 0.0)
                ram = self._status_dict.get('ram', 0.0)
                stage = self._status_dict.get('stage', '[待機]')

                indicator = f"\r\033[K<pre style='margin: 0; color: white;'>{now_time} | CPU: {cpu:.1f}% | RAM: {ram:.1f}% | {stage}</pre>"

                clear_output(wait=True)
                display(HTML(indicator))
            time.sleep(0.2) # 每秒刷新 5 次

    def update_upper_display(self, force=False):
        """更新上半部的近況彙報區"""
        critical_levels = ["INFO", "BATTLE", "SUCCESS", "WARNING", "ERROR", "CRITICAL"]
        recent_logs = self._log_manager.get_recent_logs(count=15, levels=critical_levels)

        # 只有當日誌數量變化或強制刷新時才重繪
        if len(recent_logs) != self._last_log_count or force:
            self._last_log_count = len(recent_logs)
            with self.upper_display_area:
                clear_output(wait=True)
                for log in reversed(recent_logs): # 從舊到新顯示
                    display(HTML(self._format_log_message(log)))

    def start(self):
        """啟動顯示管理器"""
        display(self.upper_display_area, self.lower_display_area)
        self._stop_event.clear()
        self._display_thread.start()
        # 初始時強制刷新一次，顯示標題
        self.update_upper_display(force=True)

    def stop(self):
        """停止顯示管理器"""
        self._stop_event.set()
        self._display_thread.join()
        # 清理最後的狀態行
        with self.lower_display_area:
            clear_output()
        print("顯示管理器已停止。")
