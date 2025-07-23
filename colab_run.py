# integrated_platform/src/colab_bootstrap.py
# -*- coding: utf-8 -*-

# --- v2.2.0 智慧整合架構 ---
# 核心理念：將環境部署的複雜性完全委託給 run.sh 和 poetry_manager.py。
#           此腳本專注於：
#           1. 啟動視覺化儀表板。
#           2. 呼叫 run.sh 執行智慧安裝。
#           3. 啟動後端服務。
#           4. 執行健康檢查並發布服務。

import argparse
import html
import os
import subprocess
import sys
import threading
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# --- 全域變數 ---
APP_VERSION = "v2.2.0"
LOG_DISPLAY_LINES = 50
STATUS_REFRESH_INTERVAL = 1.0
FASTAPI_PORT = 8000
PROJECT_FOLDER_NAME = "WEB"

STOP_EVENT = threading.Event()

# --- 日誌管理器 ---
class LogManager:
    """將日誌寫入 SQLite 資料庫，並提供版本標定。"""
    def __init__(self, db_path, version):
        self.db_path = db_path
        self.version = version
        self.lock = threading.Lock()
        self._create_table()

    def _create_table(self):
        with self.lock:
            with sqlite3.connect(self.db_path, timeout=10) as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT, version TEXT, timestamp TEXT, level TEXT, message TEXT
                );""")
                conn.commit()

    def log(self, level, message):
        ts = datetime.now(ZoneInfo("Asia/Taipei")).isoformat()
        with self.lock:
            try:
                with sqlite3.connect(self.db_path, timeout=10) as conn:
                    conn.execute("INSERT INTO logs (version, timestamp, level, message) VALUES (?, ?, ?, ?);",
                                 (self.version, ts, level, message))
                    conn.commit()
            except Exception as e:
                print(f"資料庫日誌記錄時發生嚴重錯誤: {e}", file=sys.stderr)

log_manager = None

# --- 顯示管理器 ---
class DisplayManager(threading.Thread):
    """在獨立線程中，持續從資料庫讀取日誌並更新 Colab UI。"""
    def __init__(self, db_path, stop_event):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.stop_event = stop_event
        self.last_log_id = 0
        self.last_status_update = 0
        self.taipei_tz = ZoneInfo("Asia/Taipei")
        from IPython.display import display, HTML, Javascript
        self.display = display
        self.HTML = HTML
        self.Javascript = Javascript

    def _execute_js(self, js_code):
        try:
            self.display(self.Javascript(js_code))
        except Exception:
            pass

    def setup_ui(self):
        from IPython.display import clear_output
        clear_output(wait=True)
        ui_html = f"""
        <style>
            .grid-container {{ display: grid; grid-template-columns: 10ch 11ch 1fr; gap: 0 8px; font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px; line-height: 1.6; }}
            .grid-item {{ white-space: pre; }}
            #status-bar {{ margin-top: 10px; border-top: 1px solid #444; padding-top: 4px; }}
            #portal-container {{ margin-bottom: 15px; }}
            .version-tag {{ font-weight: bold; color: #757575; margin-left: 12px; }}
        </style>
        <div id="portal-container"></div>
        <div id="log-panel" class="grid-container"></div>
        <div id="status-bar" class="grid-container"></div>
        """
        self.display(self.HTML(ui_html))

    def _update_status_bar(self):
        now = time.time()
        if now - self.last_status_update < STATUS_REFRESH_INTERVAL:
            return
        self.last_status_update = now
        try:
            import psutil
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            time_str = datetime.now(self.taipei_tz).strftime('%H:%M:%S')
            status_html = (
                f"<div class='grid-item' style='color: #FFFFFF;'>{time_str}</div>"
                f"<div class='grid-item' style='color: #FFFFFF;'>| CPU: {cpu:4.1f}%</div>"
                f"<div class='grid-item' style='color: #FFFFFF;'>| RAM: {ram:4.1f}% | [系統運行中 <span class='version-tag'>{APP_VERSION}</span>]</div>"
            )
            escaped_status_html = status_html.replace('`', '\\`')
            js_code = f"document.getElementById('status-bar').innerHTML = `{escaped_status_html}`;"
            self._execute_js(js_code)
        except Exception:
            pass

    def _update_log_panel(self):
        if not self.db_path.exists(): return
        try:
            with sqlite3.connect(self.db_path) as conn:
                new_logs = conn.execute("SELECT id, version, timestamp, level, message FROM logs WHERE id > ? ORDER BY id ASC", (self.last_log_id,)).fetchall()
            if not new_logs: return

            for log_id, version, ts, level, msg in new_logs:
                formatted_ts = datetime.fromisoformat(ts).strftime('%H:%M:%S')
                level_upper = level.upper()
                colors = {"SUCCESS": '#4CAF50', "ERROR": '#F44336', "CRITICAL": '#F44336', "WARNING": '#FBC02D', "INFO": '#B0BEC5'}
                level_color = colors.get(level_upper, '#B0BEC5')
                log_html = (
                    f"<div class='grid-item' style='color: #FFFFFF;'>[{formatted_ts}]</div>"
                    f"<div class='grid-item' style='color: {level_color}; font-weight: bold;'>[{level_upper:<8}]</div>"
                    f"<div class='grid-item' style='color: #FFFFFF;'>[{version}] {html.escape(msg)}</div>"
                )
                js_code = f"""
                const panel = document.getElementById('log-panel');
                if (panel) {{
                    const entry = document.createElement('div');
                    entry.style.display = 'contents';
                    entry.innerHTML = `{log_html.replace('`', '\\`').replace('\\n', '<br>')}`;
                    Array.from(entry.children).reverse().forEach(c => panel.prepend(c));
                    while (panel.childElementCount > ({LOG_DISPLAY_LINES} * 3)) {{
                        for(let i=0; i<3; i++) panel.removeChild(panel.lastChild);
                    }}
                }}"""
                self._execute_js(js_code)
                self.last_log_id = log_id
        except Exception:
            pass

    def run(self):
        self.setup_ui()
        while not self.stop_event.is_set():
            self._update_status_bar()
            self._update_log_panel()
            time.sleep(0.1)

# --- 核心輔助函式 ---
def print_separator(title):
    """打印一個帶有標題和符號的視覺分隔線，以美化輸出。"""
    log_manager.log("INFO", f"======= ⚡️ {title} ⚡️ =======")

def run_command(command):
    """在前景執行一個命令，並將其輸出即時串流到日誌。"""
    log_manager.log("INFO", f"準備執行指令: {' '.join(command)}")
    process = subprocess.Popen(
        command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace'
    )
    for line in iter(process.stdout.readline, ''):
        log_manager.log("INFO", f"[{command[0]}] {line.strip()}")
    process.stdout.close()
    return_code = process.wait()
    if return_code != 0:
        log_manager.log("ERROR", f"指令 '{' '.join(command)}' 執行失敗，返回碼: {return_code}")
        raise subprocess.CalledProcessError(return_code, command)
    log_manager.log("SUCCESS", f"指令 '{' '.join(command)}' 執行成功。")

def start_fastapi_server(log_manager):
    """在一個獨立的線程中啟動 FastAPI 伺服器。"""
    log_manager.log("INFO", "正在準備啟動 FastAPI 伺服器...")
    try:
        from uvicorn import Config, Server
        from integrated_platform.src.main import app
        app.state.log_manager = log_manager
        config = Config(app, host="0.0.0.0", port=FASTAPI_PORT, log_level="info")
        server = Server(config)
        thread = threading.Thread(target=server.run, daemon=True)
        thread.start()
        log_manager.log("SUCCESS", f"FastAPI 伺服器已在背景線程中啟動。")
        return thread
    except Exception as e:
        log_manager.log("CRITICAL", f"FastAPI 伺服器啟動失敗: {e}")
        raise

def health_check(log_manager):
    """執行健康檢查循環，直到服務就緒或超時。"""
    import requests
    log_manager.log("INFO", "啟動健康檢查程序...")
    start_time = time.time()
    timeout = 40
    while time.time() - start_time < timeout:
        try:
            response = requests.get(f"http://localhost:{FASTAPI_PORT}/health", timeout=2)
            if response.status_code == 200:
                log_manager.log("SUCCESS", f"健康檢查成功！後端服務已就緒。")
                return True
        except requests.exceptions.RequestException:
            log_manager.log("INFO", "服務尚未就緒，將在 2 秒後重試...")
            time.sleep(2)
    log_manager.log("CRITICAL", "健康檢查超時，服務啟動失敗。")
    return False

def create_public_portal(log_manager):
    """建立公開連結。"""
    from google.colab import output as colab_output
    from IPython.display import display, Javascript
    log_manager.log("INFO", f"奉命建立服務入口，目標埠號: {FASTAPI_PORT}...")
    try:
        with colab_output.redirect_to_element('#portal-container'):
            display(Javascript("document.getElementById('portal-container').innerHTML = '';"))
            colab_output.serve_kernel_port_as_iframe(FASTAPI_PORT, path='/', height=500)
        log_manager.log("SUCCESS", f"服務入口已成功建立！")
    except Exception as e:
        log_manager.log("CRITICAL", f"建立服務入口的嘗試失敗: {e}")

# --- 主流程 ---
def main():
    """智慧整合架構的主執行流程。"""
    global log_manager
    project_root = Path(os.getcwd())
    db_path = project_root / "logs.sqlite"
    if db_path.exists(): db_path.unlink()
    log_manager = LogManager(db_path=db_path, version=APP_VERSION)
    start_time_str = datetime.now(ZoneInfo("Asia/Taipei")).strftime('%Y-%m-%d %H:%M:%S')
    log_manager.log("INFO", f"作戰流程開始 (版本 {APP_VERSION}，啟動於 {start_time_str})。")

    # --- 階段一：初始化儀表板 ---
    print_separator("正在初始化戰情儀表板")
    display_thread = DisplayManager(db_path, STOP_EVENT)
    display_thread.start()
    time.sleep(1)

    try:
        # --- 階段二：執行環境部署 ---
        print_separator("正在執行環境部署 (日誌由 run.sh 提供)")
        run_command(["bash", "run.sh"])

        # --- 階段三：啟動後端服務 ---
        print_separator("正在啟動後端 FastAPI 服務")
        start_fastapi_server(log_manager)

        # --- 階段四：健康檢查與服務發布 ---
        print_separator("正在進行健康檢查")
        if not health_check(log_manager):
            raise RuntimeError("後端服務健康檢查失敗。")

        print_separator("發布服務入口")
        create_public_portal(log_manager)

        log_manager.log("SUCCESS", "✅ 作戰平台已成功啟動。要停止所有服務，請點擊此儲存格的「中斷執行」(■) 按鈕。")
        while not STOP_EVENT.is_set():
            time.sleep(1)

    except (KeyboardInterrupt, SystemExit):
        log_manager.log("INFO", "\n[偵測到使用者手動中斷請求...]")
    except Exception as e:
        import traceback
        log_manager.log("CRITICAL", f"作戰流程發生未預期的嚴重錯誤: {e}")
        log_manager.log("CRITICAL", traceback.format_exc())
    finally:
        STOP_EVENT.set()
        if 'display_thread' in locals() and display_thread.is_alive():
            display_thread.join(timeout=2)
        end_time_str = datetime.now(ZoneInfo("Asia/Taipei")).strftime('%Y-%m-%d %H:%M:%S')
        log_manager.log("INFO", f"作戰流程結束 (結束於 {end_time_str})。")
        print("\n--- 所有流程已結束 ---")

if __name__ == "__main__":
    print("此腳本應作為模組被 Colab 儲存格導入並執行 main() 函式。")
    print("直接執行此腳本不會啟動 Colab 的前端顯示。")
    pass
