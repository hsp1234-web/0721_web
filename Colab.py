# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 鳳凰之心 - 精準指示器 v18.0.0                                   ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   全新架構：高頻狀態與低頻事件分離顯示，後端完整記錄，體驗與穩定性兼顧。
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心 v18.0.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown > **點擊此儲存格左側的「執行」按鈕，啟動所有程序。**
#@markdown ---

import os
import sys
import shutil
import subprocess
import threading
import time
from pathlib import Path
import psutil
from IPython.display import display, clear_output
import ipywidgets as widgets
from datetime import datetime
import pytz
import sqlite3
from collections import deque

# ==============================================================================
# ⚙️ 核心管理器 (從 managers.py 和 db_logger.py 整合)
# ==============================================================================

class LogManager:
    """中央日誌管理器，負責處理、緩衝和分發日誌訊息"""
    def __init__(self, buffer_size=200):
        self.log_buffer = deque(maxlen=buffer_size)
        self._lock = threading.Lock()
        self.taipei_tz = pytz.timezone("Asia/Taipei")

    def get_taipei_time(self):
        now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
        return now_utc.astimezone(self.taipei_tz)

    def log(self, level, message, status_dict=None, stage=None):
        """記錄一條新的日誌，並可選擇性地更新狀態字典"""
        now_taipei = self.get_taipei_time()
        log_entry = {
            "timestamp": now_taipei.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
            "level": level.upper(),
            "message": message
        }
        with self._lock:
            self.log_buffer.append(log_entry)
            if status_dict is not None and stage:
                status_dict['stage'] = f"[{stage}] {message}"

    def get_all_logs(self):
        with self._lock:
            return list(self.log_buffer)

    def get_recent_display_logs(self, count=15):
        """只獲取用於顯示的關鍵日誌"""
        critical_levels = {"INFO", "BATTLE", "SUCCESS", "WARNING", "ERROR", "CRITICAL"}
        with self._lock:
            # 高效地從後向前過濾
            return [log for log in reversed(self.log_buffer) if log['level'] in critical_levels][:count]


class DatabaseLogger:
    """獨立的資料庫記錄器"""
    def __init__(self, db_path, log_manager, status_dict):
        self._db_path = db_path
        self._log_manager = log_manager
        self._status_dict = status_dict
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run)
        self._processed_log_timestamps = set()

    def _setup_database(self):
        with sqlite3.connect(self._db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("CREATE TABLE IF NOT EXISTS hardware_log (timestamp TEXT, cpu REAL, ram REAL)")
            cursor.execute("CREATE TABLE IF NOT EXISTS event_log (timestamp TEXT, level TEXT, message TEXT)")
            conn.commit()

    def _run(self):
        self._setup_database()
        while not self._stop_event.is_set():
            try:
                with sqlite3.connect(self._db_path, timeout=5) as conn:
                    cursor = conn.cursor()
                    ts = self._log_manager.get_taipei_time().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    cursor.execute("INSERT INTO hardware_log VALUES (?, ?, ?)", (ts, self._status_dict['cpu'], self._status_dict['ram']))

                    logs_to_process = self._log_manager.get_all_logs()
                    for log in logs_to_process:
                        if log['timestamp'] not in self._processed_log_timestamps:
                            cursor.execute("INSERT INTO event_log VALUES (?, ?, ?)", (log['timestamp'], log['level'], log['message']))
                            self._processed_log_timestamps.add(log['timestamp'])
                    conn.commit()
            except Exception as e:
                # 在主控台打印資料庫錯誤，但不影響主程序
                print(f"資料庫記錄錯誤: {e}")
            time.sleep(2) # 每 2 秒寫入一次

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self._thread.join()

class DisplayManager:
    """顯示管理器，負責在 Colab 中智能地渲染雙區塊儀表板"""
    def __init__(self, log_manager, status_dict):
        self._log_manager = log_manager
        self._status_dict = status_dict
        self._stop_event = threading.Event()
        self._live_indicator_thread = threading.Thread(target=self._run_live_indicator)
        self.upper_area = widgets.Output()
        self.lower_area = widgets.Output()
        self._last_log_count = -1
        self._last_update_time = 0

    def _format_log_html(self, log):
        colors = {"SUCCESS": "#34a853", "WARNING": "#fbbc04", "ERROR": "#ea4335", "CRITICAL": "#ea4335", "BATTLE": "#4285f4"}
        color = colors.get(log['level'], "white")
        weight = "bold" if log['level'] in ["CRITICAL", "BATTLE"] else "normal"
        return f"<pre style='margin: 0; white-space: pre-wrap; color: {color}; font-weight: {weight};'>[{log['timestamp']}] [{log['level']}] {log['message']}</pre>"

    def _run_live_indicator(self):
        """高頻刷新下半部的即時狀態行"""
        while not self._stop_event.is_set():
            self._status_dict['cpu'] = psutil.cpu_percent()
            self._status_dict['ram'] = psutil.virtual_memory().percent

            with self.lower_area:
                now = self._log_manager.get_taipei_time().strftime('%H:%M:%S')
                stage_text = self._status_dict.get('stage', '[初始化中...]')
                indicator_html = f"""<pre style='margin: 0; color: white;'>{now} | CPU: {self._status_dict['cpu']:.1f}% | RAM: {self._status_dict['ram']:.1f}% | {stage_text}</pre>"""
                clear_output(wait=True)
                display(HTML(indicator_html))
            self.update_upper_display()
            time.sleep(0.5) # 每 0.5 秒刷新一次

    def update_upper_display(self, force=False):
        """低頻更新上半部的近況彙報區"""
        now = time.time()
        recent_logs = self._log_manager.get_recent_display_logs(15)
        if force or (len(recent_logs) != self._last_log_count and now - self._last_update_time > 1):
            self._last_log_count = len(recent_logs)
            self._last_update_time = now
            with self.upper_area:
                clear_output(wait=True)
                for log in reversed(recent_logs):
                    display(HTML(self._format_log_html(log)))

    def start(self):
        display(self.upper_area, self.lower_area)
        self._live_indicator_thread.start()

    def stop(self):
        self._stop_event.set()
        self._live_indicator_thread.join()

# ==============================================================================
# 🚀 主執行邏輯
# ==============================================================================

def generate_final_report(db_path, log_manager):
    """從資料庫生成最終的純文字報告"""
    if not db_path.exists():
        log_manager.log("ERROR", "找不到資料庫檔案，無法生成最終報告。")
        return

    report_filename = f"report_{log_manager.get_taipei_time().strftime('%Y%m%d_%H%M%S')}.txt"
    log_manager.log("INFO", f"正在生成最終報告: {report_filename}")

    with open(report_filename, "w", encoding="utf-8") as f, sqlite3.connect(db_path) as conn:
        f.write("="*80 + "\n")
        f.write("鳳凰之心 - 最終執行報告\n")
        f.write("="*80 + "\n\n")

        f.write("--- 事件日誌 ---\n")
        cursor = conn.cursor()
        for row in cursor.execute("SELECT * FROM event_log ORDER BY timestamp ASC"):
            f.write(f"[{row[0]}] [{row[1]}] {row[2]}\n")

        f.write("\n--- 硬體監控記錄 (每分鐘抽樣) ---\n")
        # 為了報告簡潔，只抽樣部分硬體數據
        for row in cursor.execute("SELECT * FROM hardware_log WHERE CAST(strftime('%S', timestamp) AS INTEGER) % 60 == 0"):
             f.write(f"[{row[0]}] CPU: {row[1]:.1f}%, RAM: {row[2]:.1f}%\n")

    log_manager.log("SUCCESS", f"最終報告已儲存至 {report_filename}")


def main():
    # --- 1. 初始化核心組件 ---
    status_dict = {'cpu': 0.0, 'ram': 0.0, 'stage': '[啟動中]'}
    log_manager = LogManager()
    display_manager = DisplayManager(log_manager, status_dict)

    db_path = Path("logs.sqlite")
    if db_path.exists(): os.remove(db_path) # 每次都使用全新的資料庫

    db_logger = DatabaseLogger(db_path, log_manager, status_dict)

    # --- 2. 啟動並執行 ---
    try:
        display_manager.start()
        db_logger.start()

        log_manager.log("INFO", "鳳凰之心 v18.0.0 初始化...", status_dict, "啟動")
        time.sleep(2)

        # --- 模擬核心業務邏輯 ---
        log_manager.log("BATTLE", "開始執行核心任務...", status_dict, "執行中")

        log_manager.log("INFO", "步驟 1/3: 正在下載數據...", status_dict, "下載")
        time.sleep(3)

        log_manager.log("INFO", "步驟 2/3: 正在分析市場情緒...", status_dict, "分析")
        time.sleep(4)
        if time.time() % 10 < 3: # 模擬隨機錯誤
             log_manager.log("ERROR", "數據源 API 連線超時 (模擬錯誤)", status_dict, "錯誤")
             raise ConnectionError("API connection failed")

        log_manager.log("INFO", "步驟 3/3: 正在生成交易策略...", status_dict, "生成策略")
        time.sleep(3)

        log_manager.log("SUCCESS", "所有核心任務已成功完成。", status_dict, "完成")

    except KeyboardInterrupt:
        log_manager.log("WARNING", "偵測到手動中斷！", status_dict, "中斷")
    except Exception as e:
        log_manager.log("CRITICAL", f"發生未預期的嚴重錯誤: {e}", status_dict, "嚴重錯誤")
    finally:
        # --- 3. 優雅地關閉與清理 ---
        log_manager.log("INFO", "正在關閉所有服務...", status_dict, "關閉中")
        display_manager.stop()
        db_logger.stop()
        generate_final_report(db_path, log_manager)
        print("\n所有程序已結束。")

if __name__ == "__main__":
    main()
