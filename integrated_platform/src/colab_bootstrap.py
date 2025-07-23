# integrated_platform/src/colab_bootstrap.py
# -*- coding: utf-8 -*-

# ==============================================================================
# SECTION 0: 環境初始化與核心模組導入
# ==============================================================================
import os
import sys
import subprocess
import threading
import time
import sqlite3
import psutil
import traceback
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from collections import deque
import html

# Colab 專用模組
from IPython.display import display, HTML, Javascript, clear_output
from google.colab import output as colab_output

# --- 全域常數與設定 ---
# [作戰藍圖 244-H] 加入版本號
APP_VERSION = "v1.9.1"
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔"
FASTAPI_PORT = 8000
LOG_DISPLAY_LINES = 15
STATUS_REFRESH_INTERVAL = 1.0
ARCHIVE_DIR = Path("/content") / ARCHIVE_FOLDER_NAME
TAIPEI_TZ = ZoneInfo("Asia/Taipei")
STOP_EVENT = threading.Event()

# ==============================================================================
# SECTION 1: 後端日誌管理器
# ==============================================================================
class LogManager:
    """負責將日誌安全地寫入中央 SQLite 資料庫。"""
    def __init__(self, db_path):
        self.db_path = db_path
        self.lock = threading.Lock()
        self._create_table()

    def _get_connection(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _create_table(self):
        with self.lock:
            with self._get_connection() as conn:
                conn.execute("""
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    level TEXT NOT NULL,
                    message TEXT NOT NULL
                );
                """)
                conn.commit()

    def log(self, level, message):
        ts = datetime.now(TAIPEI_TZ).isoformat()
        with self.lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?);", (ts, level, message))
                    conn.commit()
            except Exception as e:
                print(f"CRITICAL DB LOGGING ERROR: {e}")

# ==============================================================================
# SECTION 2: 智慧顯示管理器
# ==============================================================================
class DisplayManager(threading.Thread):
    """在獨立執行緒中，作為唯一的「畫家」，持續從資料庫讀取日誌並更新前端UI。"""
    def __init__(self, db_path, display_lines, refresh_interval, stop_event):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.display_lines = max(1, display_lines)
        self.refresh_interval = max(0.1, refresh_interval)
        self.stop_event = stop_event
        self.last_log_id = 0
        self.last_status_update = 0

    def _execute_js(self, js_code):
        try: display(Javascript(js_code))
        except Exception: pass

    def setup_ui(self):
        clear_output(wait=True)
        # [作戰藍圖 244-H] 在 UI 中加入版本號
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
        display(HTML(ui_html))

    def _update_status_bar(self):
        now = time.time()
        if now - self.last_status_update < self.refresh_interval: return
        self.last_status_update = now
        try:
            cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
            time_str = datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')
            # [作戰藍圖 244-H] 在狀態列加入版本號
            status_html = f"<div class='grid-item' style='color: #FFFFFF;'>{time_str}</div>" \
                          f"<div class='grid-item' style='color: #FFFFFF;'>| CPU: {cpu:4.1f}%</div>" \
                          f"<div class='grid-item' style='color: #FFFFFF;'>| RAM: {ram:4.1f}% | [系統運行中 <span class='version-tag'>{APP_VERSION}</span>]</div>"
            escaped_html = status_html.replace('`', '\\`')
            js_code = f"document.getElementById('status-bar').innerHTML = `{escaped_html}`;"
            self._execute_js(js_code)
        except Exception: pass

    def _update_log_panel(self):
        if not self.db_path.exists(): return
        try:
            with sqlite3.connect(self.db_path) as conn:
                new_logs = conn.execute("SELECT id, timestamp, level, message FROM logs WHERE id > ? ORDER BY id ASC", (self.last_log_id,)).fetchall()
            if not new_logs: return
            for log_id, ts, level, msg in new_logs:
                formatted_ts = datetime.fromisoformat(ts).strftime('%H:%M:%S')
                level_upper = level.upper()
                colors = {{"SUCCESS": '#4CAF50', "ERROR": '#F44336', "CRITICAL": '#F44336', "WARNING": '#FBC02D', "INFO": '#B0BEC5'}}
                level_color = colors.get(level_upper, '#B0BEC5')
                # [作戰藍圖 244-H] 調整日誌對齊
                log_html = f"<div class='grid-item' style='color: #FFFFFF;'>[{formatted_ts}]</div>" \
                           f"<div class='grid-item' style='color: {level_color}; font-weight: bold;'>[{level_upper:<8}]</div>" \
                           f"<div class='grid-item' style='color: #FFFFFF;'>{html.escape(msg)}</div>"
                escaped_log_html = log_html.replace('`', '\\`')
                js_code = f"""
                const panel = document.getElementById('log-panel');
                if (panel) {{
                    const entry = document.createElement('div');
                    entry.style.display = 'contents';
                    entry.innerHTML = `{escaped_log_html}`;
                    Array.from(entry.children).reverse().forEach(c => panel.prepend(c));
                    while (panel.childElementCount > ({self.display_lines} * 3)) {{
                        for(let i=0; i<3; i++) panel.removeChild(panel.lastChild);
                    }}
                }}"""
                self._execute_js(js_code)
                self.last_log_id = log_id
        except Exception: pass

    def run(self):
        self.setup_ui()
        while not self.stop_event.is_set():
            self._update_status_bar()
            self._update_log_panel()
            time.sleep(0.1)

# ==============================================================================
# SECTION 3: 公開服務入口建立官
# ==============================================================================
def create_public_portal(port, max_retries=5, delay_seconds=3):
    """以高可靠性的方式，嘗試為指定的埠號建立一個公開的 Colab 代理連結。"""
    global log_manager
    log_manager.log("INFO", f"奉命建立服務入口，目標埠號: {port}...")
    button_html = """
    <style>
        .portal-button {{ background: linear-gradient(145deg, #2e6cdf, #4a8dff); border: none; border-radius: 8px; color: white; padding: 12px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; font-weight: bold; font-family: 'Segoe UI', 'Noto Sans TC', sans-serif; margin: 4px 2px; cursor: pointer; box-shadow: 0 4px 15px 0 rgba(74, 144, 255, 0.45); transition: all 0.3s ease; }}
        .portal-button:hover {{ background: linear-gradient(145deg, #4a8dff, #2e6cdf); box-shadow: 0 6px 20px 0 rgba(74, 144, 255, 0.6); transform: translateY(-2px); }}
    </style>
    <a href="{url}" target="_blank" class="portal-button">🚀 進入鳳凰轉錄儀作戰中心 ({version})</a>
    """
    for attempt in range(max_retries):
        try:
            with colab_output.redirect_to_element('#portal-container'):
                colab_output.clear()
                colab_output.serve_kernel_port_as_window(port, path='/')
            from google.colab import _kernel
            base_url = _kernel.get_parent_request_header()['Referer'].split('?')[0]
            public_url = f"{{base_url}}proxy/{{port}}/"
            with colab_output.redirect_to_element('#portal-container'):
                display(HTML(button_html.format(url=public_url, version=APP_VERSION)))
            log_manager.log("SUCCESS", f"服務入口已成功建立！")
            return
        except Exception as e:
            log_manager.log("WARNING", f"建立入口嘗試 #{attempt + 1} 失敗...")
            if attempt < max_retries - 1:
                time.sleep(delay_seconds)
            else:
                log_manager.log("CRITICAL", "所有建立服務入口的嘗試均告失敗。")
                with colab_output.redirect_to_element('#portal-container'):
                     display(HTML("<p style='color:#F44336;'><b>錯誤：</b>無法建立公開連結。</p>"))

# ==============================================================================
# SECTION 4: 核心輔助函式
# ==============================================================================
def archive_final_log(db_path):
    """在作戰結束時，將所有日誌從資料庫匯出為 .txt 檔案。"""
    log_manager.log("INFO", "正在生成最終作戰報告...")
    if not db_path.is_file(): return
    try:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
        archive_filename = f"作戰日誌_{datetime.now(TAIPEI_TZ).strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        archive_filepath = ARCHIVE_DIR / archive_filename
        with sqlite3.connect(db_path) as conn:
            logs = conn.execute("SELECT timestamp, level, message FROM logs ORDER BY id ASC").fetchall()
        with open(archive_filepath, 'w', encoding='utf-8') as f:
            for ts, lvl, msg in logs: f.write(f"[{ts}] [{lvl.upper()}] {msg}\\n")
        log_manager.log("SUCCESS", f"完整日誌已歸檔至: {archive_filepath}")
    except Exception as e:
        log_manager.log("ERROR", f"歸檔日誌時發生錯誤: {e}")

def find_project_path():
    """動態偵測 run.sh 的位置以確定專案根目錄。"""
    log_manager.log("INFO", "正在動態偵測專案路徑...")
    search_root = Path("/content")
    found_scripts = list(search_root.rglob('run.sh'))

    if not found_scripts:
        raise FileNotFoundError(f"致命錯誤：在 '{{search_root}}' 目錄下找不到任何 'run.sh' 部署腳本！")

    if len(found_scripts) > 1:
        log_manager.log("WARNING", f"偵測到多個 run.sh 腳本，將使用第一個: {found_scripts[0]}")

    run_script_path = found_scripts[0]
    project_path = run_script_path.parent
    log_manager.log("SUCCESS", f"專案路徑已鎖定: {project_path}")
    return project_path, run_script_path

# ==============================================================================
# SECTION 5: 作戰主流程
# ==============================================================================
def main():
    global log_manager, display_thread, SQLITE_DB_PATH
    log_manager = None
    display_thread = None
    SQLITE_DB_PATH = None

    try:
        # 1. 初始化日誌系統 (使用暫存日誌路徑)
        temp_db_path = Path("/content/temp_logs.sqlite")
        if temp_db_path.exists(): temp_db_path.unlink()
        log_manager = LogManager(temp_db_path)

        # 2. 立即啟動智慧顯示管理器
        display_thread = DisplayManager(temp_db_path, LOG_DISPLAY_LINES, STATUS_REFRESH_INTERVAL, STOP_EVENT)
        display_thread.start()
        time.sleep(0.5)

        # 3. 動態偵測專案路徑
        PROJECT_PATH, RUN_SCRIPT_PATH = find_project_path()

        # 確定最終的日誌路徑並重新設定
        SQLITE_DB_PATH = PROJECT_PATH / "logs.sqlite"
        if SQLITE_DB_PATH.exists(): SQLITE_DB_PATH.unlink()
        log_manager.db_path = SQLITE_DB_PATH
        log_manager._create_table()
        display_thread.db_path = SQLITE_DB_PATH

        # 4. 設定環境變數，讓後端知道日誌資料庫的路徑
        os.environ['LOG_DB_PATH'] = str(SQLITE_DB_PATH)
        os.environ['UVICORN_PORT'] = str(FASTAPI_PORT)

        # 5. 執行後端部署
        log_manager.log("INFO", "正在執行後端部署腳本 (run.sh)...")
        # [作戰藍圖 244-J] 新增 cwd=PROJECT_PATH 參數
        # 這確保 run.sh 在正確的專案根目錄下執行，以便 poetry 能找到 pyproject.toml
        result = subprocess.run(
            ["bash", str(RUN_SCRIPT_PATH)],
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=PROJECT_PATH
        )
        if result.returncode != 0:
            log_manager.log("ERROR", "後端部署腳本執行失敗。")
            log_manager.log("ERROR", f"詳細錯誤: {result.stderr.strip()}")
            raise RuntimeError("後端部署失敗，請檢查日誌。")
        log_manager.log("SUCCESS", "後端部署腳本執行完畢。")

        # 6. 呼叫入口建立官
        create_public_portal(port=FASTAPI_PORT)

        # 7. 保持儲存格運行
        log_manager.log("SUCCESS", f"作戰系統已上線！({APP_VERSION}) 要停止所有服務，請點擊此儲存格的「中斷執行」(■) 按鈕。")
        while not STOP_EVENT.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        if log_manager: log_manager.log("INFO", "\\n[偵測到使用者手動中斷請求...]")
    except Exception as e:
        if log_manager:
            log_manager.log("CRITICAL", f"作戰流程發生未預期的嚴重錯誤: {e}")
            log_manager.log("CRITICAL", traceback.format_exc())
        print(f"\\n💥 作戰流程發生未預期的嚴重錯誤，系統即將終止。")
        traceback.print_exc()
        time.sleep(1)
    finally:
        STOP_EVENT.set()
        if log_manager and SQLITE_DB_PATH:
            log_manager.log("INFO", "[正在執行終端清理與日誌歸檔程序...]")
            archive_final_log(SQLITE_DB_PATH)
            log_manager.log("SUCCESS", "部署流程已結束，所有服務已安全關閉。")
        if display_thread:
            display_thread.join(timeout=2)

if __name__ == "__main__":
    main()
