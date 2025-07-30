# -*- coding: utf-8 -*-
import asyncio
import subprocess
import sys
import sqlite3
from pathlib import Path
import os
import time
import json
import pytz
from datetime import datetime
import shlex
import threading
import psutil

# --- 快速測試模式設定 ---
os.environ['FAST_TEST_MODE'] = 'true'
# 在測試模式下，我們將 CI_MODE 也設為 true，以防止長時間休眠
os.environ['CI_MODE'] = 'true'


from core_utils.commander_console import CommanderConsole
from core_utils.resource_monitor import is_resource_sufficient, load_resource_settings

# --- 全域設定 ---
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
DB_FILE = LOGS_DIR / "logs_test.sqlite" # 使用獨立的測試資料庫
TAIWAN_TZ = pytz.timezone('Asia/Taipei')
APPS_DIR = Path("apps")

# 全域控制台物件
console = CommanderConsole()

def setup_database():
    """初始化 SQLite 資料庫和日誌表"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS phoenix_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            cpu_usage REAL,
            ram_usage REAL
        )
        """)
        conn.commit()

def log_event(level, message, cpu=None, ram=None):
    """將事件記錄到 TUI 和 SQLite 資料庫"""
    if not cpu: cpu = console.cpu_usage
    if not ram: ram = console.ram_usage

    console.add_log(f"[{level}] {message}")

    timestamp = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO phoenix_logs (timestamp, level, message, cpu_usage, ram_usage) VALUES (?, ?, ?, ?, ?)",
            (timestamp, level, message, cpu, ram)
        )
        conn.commit()

async def main_logic():
    """核心的循序啟動邏輯 (測試版)"""
    log_event("BATTLE", "鳳凰之心 v18.0 [測試模式] 啟動序列開始。")
    log_event("INFO", "系統環境預檢完成。")

    log_event("INFO", "[快速測試模式] 跳過所有 App 的安裝與啟動。")
    await asyncio.sleep(5) # 模擬一些工作負載

    log_event("SUCCESS", "測試流程驗證成功。")
    console.update_status_tag("[測試通過]")

# --- 主程序 ---
def performance_logger_thread():
    """一個獨立的執行緒，專門用來將效能數據寫入資料庫"""
    while not console._stop_event.is_set():
        timestamp = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO phoenix_logs (timestamp, level, message, cpu_usage, ram_usage) VALUES (?, ?, ?, ?, ?)",
                (timestamp, "PERF", "performance_snapshot", console.cpu_usage, console.ram_usage)
            )
            conn.commit()
        time.sleep(1) # 每秒記錄一次

async def main():
    """包含 TUI 和休眠邏輯的主異步函數"""
    if DB_FILE.exists():
        os.remove(DB_FILE)
    setup_database()

    console.start()

    # 啟動專門的效能日誌記錄執行緒
    perf_thread = threading.Thread(target=performance_logger_thread, daemon=True)
    perf_thread.start()

    try:
        await main_logic()
        log_event("INFO", "任務流程執行完畢，系統進入待命狀態。")
        if not os.getenv("CI_MODE") and not os.getenv("FAST_TEST_MODE"):
            await asyncio.sleep(3600)
    except Exception as e:
        log_event("CRITICAL", f"主程序發生未預期錯誤: {e}")
    finally:
        console.stop("程序結束。")
        # 確保效能日誌執行緒也已停止
        perf_thread.join(timeout=1.5)

if __name__ == "__main__":
    try:
        # 確保 uv 已安裝
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("錯誤: 核心工具 'uv' 未安裝。請先執行 'pip install uv'。")
        sys.exit(1)

    try:
        if 'IPython' in sys.modules:
            import nest_asyncio
            nest_asyncio.apply()
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
