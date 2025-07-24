# -*- coding: utf-8 -*-
# 最終作戰計畫 P8：鳳凰之心
# 核心引擎 (core_run.py)

import logging
import subprocess
import sys
import threading
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# --- 全域常數 ---
APP_VERSION = "v3.0.0-Phoenix"
FASTAPI_PORT = 8000
DB_PATH = Path("logs.sqlite")
STOP_EVENT = threading.Event()

# --- 日誌管理器 ---
class LogManager:
    """將日誌統一寫入 SQLite 資料庫，具備執行緒安全。"""
    def __init__(self, db_path, version):
        self.db_path = db_path
        self.version = version
        self.lock = threading.Lock()
        self.taipei_tz = ZoneInfo("Asia/Taipei")
        self._create_table()
        self.log("INFO", f"日誌管理器初始化完成 (版本: {self.version})。")

    def _create_table(self):
        with self.lock:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    version TEXT,
                    timestamp TEXT,
                    level TEXT,
                    message TEXT
                );""")
                conn.commit()

    def log(self, level, message):
        ts = datetime.now(self.taipei_tz).isoformat()
        with self.lock:
            try:
                with sqlite3.connect(self.db_path, timeout=10) as conn:
                    conn.execute(
                        "INSERT INTO logs (version, timestamp, level, message) VALUES (?, ?, ?, ?);",
                        (self.version, ts, level, message)
                    )
                    conn.commit()
            except Exception as e:
                # 如果資料庫日誌失敗，退回到標準錯誤輸出
                print(f"CRITICAL: 資料庫日誌記錄失敗: {e}", file=sys.stderr)
                print(f"Original Log: [{level}] {message}", file=sys.stderr)

log_manager = None

# --- 核心輔助函式 ---
def print_separator(title):
    """打印一個帶有標題的視覺分隔線到日誌。"""
    log_manager.log("INFO", f"======= 🚀 {title} 🚀 =======")

def start_fastapi_server():
    """在一個獨立的線程中啟動 FastAPI 伺服器。"""
    log_manager.log("INFO", "準備啟動 FastAPI 伺服器...")
    try:
        from uvicorn import Config, Server
        # 延遲導入，以避免在非 poetry 環境中直接執行此腳本時出錯
        from integrated_platform.src.main import app

        # 將 log_manager 注入到 app 的 state 中，以便在 API 路由中使用
        app.state.log_manager = log_manager

        config = Config(app, host="0.0.0.0", port=FASTAPI_PORT, log_level="warning")
        server = Server(config)

        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()

        log_manager.log("SUCCESS", f"FastAPI 伺服器已在背景線程中成功啟動。")
        return thread
    except ImportError as e:
        log_manager.log("CRITICAL", f"啟動 FastAPI 失敗：缺少必要的模組 - {e}。請確保已執行 'bash run.sh' 來安裝依賴。")
        raise
    except Exception as e:
        log_manager.log("CRITICAL", f"FastAPI 伺服器啟動時發生未預期的嚴重錯誤: {e}")
        raise

def health_check():
    """執行健康檢查循環，直到服務就緒或超時。"""
    # 延遲導入 requests，因為它是由 poetry 安裝的
    try:
        import requests
    except ImportError:
        log_manager.log("CRITICAL", "缺少 'requests' 模組。無法執行健康檢查。")
        return False

    log_manager.log("INFO", "啟動健康檢查程序...")
    start_time = time.time()
    timeout = 40  # 秒

    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{FASTAPI_PORT}/health", timeout=2)
            if response.status_code == 200:
                log_manager.log("SUCCESS", "健康檢查成功！後端服務已就緒。")
                return True
        except requests.exceptions.RequestException:
            log_manager.log("INFO", "服務尚未就緒，將在 2 秒後重試...")
            time.sleep(2)

    log_manager.log("CRITICAL", "健康檢查超時，服務啟動失敗。")
    return False

# --- 主流程 ---
def main():
    """核心引擎的主執行流程。"""
    global log_manager

    # --- 階段一：初始化日誌系統 ---
    # 在任何操作之前，首先建立日誌系統
    if DB_PATH.exists():
        DB_PATH.unlink()
    log_manager = LogManager(db_path=DB_PATH, version=APP_VERSION)

    start_time_str = datetime.now(log_manager.taipei_tz).strftime('%Y-%m-%d %H:%M:%S')
    log_manager.log("INFO", f"核心引擎啟動 (版本 {APP_VERSION}，啟動於 {start_time_str})。")

    try:
        # --- 階段二：啟動後端服務 ---
        print_separator("正在啟動後端 FastAPI 服務")
        start_fastapi_server()

        # --- 階段三：健康檢查 ---
        print_separator("正在進行健康檢查")
        if not health_check():
            raise RuntimeError("後端服務健康檢查失敗，無法繼續。")

        print_separator("發布服務")
        log_manager.log("SUCCESS", f"✅ 核心引擎已成功啟動。服務運行於 http://localhost:{FASTAPI_PORT}")
        log_manager.log("INFO", "核心引擎正在運行... 按 Ctrl+C 以停止。")

        # --- 階段四：維持運行 ---
        # 保持主線程活躍，直到收到停止信號
        while not STOP_EVENT.is_set():
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        log_manager.log("INFO", "\n[偵測到手動中斷或系統退出請求...]")
    except Exception as e:
        import traceback
        log_manager.log("CRITICAL", f"核心引擎發生未預期的嚴重錯誤: {e}")
        log_manager.log("CRITICAL", traceback.format_exc())
    finally:
        STOP_EVENT.set()
        end_time_str = datetime.now(log_manager.taipei_tz).strftime('%Y-%m-%d %H:%M:%S')
        log_manager.log("INFO", f"核心引擎關閉 (結束於 {end_time_str})。")
        print("\n--- 核心引擎已停止 ---")

if __name__ == "__main__":
    print("🔵 [資訊] 此為核心引擎模組。")
    print("🔵 [資訊] 請透過 `poetry run python core_run.py` 來啟動。")
    print("🔵 [資訊] 或在 Colab 環境中，由 `colab_run.py` 來間接啟動。")
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        pass
