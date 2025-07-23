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
# [作戰藍圖 244-X] 新增版本號，用於追蹤與驗證
APP_VERSION = "v1.9.3"
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
    def __init__(self, db_path, version):
        self.db_path = db_path
        self.version = version
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
                    version TEXT NOT NULL,
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
                    conn.execute("INSERT INTO logs (version, timestamp, level, message) VALUES (?, ?, ?, ?);",
                                 (self.version, ts, level, message))
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
                # [作戰藍圖 244-X] 讀取 version 欄位
                new_logs = conn.execute("SELECT id, version, timestamp, level, message FROM logs WHERE id > ? ORDER BY id ASC", (self.last_log_id,)).fetchall()
            if not new_logs: return
            for log_id, version, ts, level, msg in new_logs:
                formatted_ts = datetime.fromisoformat(ts).strftime('%H:%M:%S')
                level_upper = level.upper()
                colors = {{"SUCCESS": '#4CAF50', "ERROR": '#F44336', "CRITICAL": '#F44336', "WARNING": '#FBC02D', "INFO": '#B0BEC5'}}
                level_color = colors.get(level_upper, '#B0BEC5')
                # [作戰藍圖 244-X] 在日誌中顯示版本號
                log_html = f"<div class='grid-item' style='color: #FFFFFF;'>[{formatted_ts}]</div>" \
                           f"<div class='grid-item' style='color: {level_color}; font-weight: bold;'>[{level_upper:<8}]</div>" \
                           f"<div class='grid-item' style='color: #FFFFFF;'>[{version}] {html.escape(msg)}</div>"
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
# SECTION 3: 公開服務入口建立官 (現代化)
# ==============================================================================
def create_public_portal(port, max_retries=5, delay_seconds=3):
    """
    [作戰藍圖 244-X] 採用 colab 建議的 serve_kernel_port_as_iframe，
    以高可靠性的方式，嘗試為指定的埠號建立一個公開的 Colab 代理連結。
    """
    global log_manager
    log_manager.log("INFO", f"奉命建立服務入口，目標埠號: {port}...")

    for attempt in range(max_retries):
        try:
            with colab_output.redirect_to_element('#portal-container'):
                display(Javascript("document.getElementById('portal-container').innerHTML = '';"))
                colab_output.serve_kernel_port_as_iframe(port, path='/', height=500)
            log_manager.log("SUCCESS", f"服務入口已成功建立！(採用 iframe 模式)")
            info_html = f"""
            <p style="font-family: 'Segoe UI', 'Noto Sans TC', sans-serif; font-size: 16px;">
                <b>🚀 鳳凰轉錄儀作戰中心已上線 (版本: {APP_VERSION})</b><br>
                請點擊上方由 Colab 生成的 <code>https://...</code> 連結進入介面。
            </p>
            """
            display(HTML(info_html))
            return
        except Exception as e:
            log_manager.log("WARNING", f"建立入口嘗試 #{attempt + 1} 失敗: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay_seconds)
            else:
                log_manager.log("CRITICAL", "所有建立服務入口的嘗試均告失敗。")
                error_html = f"<p style='color:#F44336; font-family: sans-serif;'><b>錯誤：</b>無法建立公開連結。({APP_VERSION})</p>"
                display(HTML(error_html))

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
            logs = conn.execute("SELECT version, timestamp, level, message FROM logs ORDER BY id ASC").fetchall()
        with open(archive_filepath, 'w', encoding='utf-8') as f:
            for ver, ts, lvl, msg in logs: f.write(f"[{ver}] [{ts}] [{lvl.upper()}] {msg}\\n")
        log_manager.log("SUCCESS", f"完整日誌已歸檔至: {archive_filepath}")
    except Exception as e:
        log_manager.log("ERROR", f"歸檔日誌時發生錯誤: {e}")

def find_project_path():
    """
    [作戰藍圖 244-Y] 智慧型專案路徑偵測。
    不僅尋找 run.sh，還會驗證核心應用程式是否存在，以確保找到的是真正有效的專案根目錄。
    """
    log_manager.log("INFO", "正在執行智慧型專案路徑偵測...")
    search_root = Path("/content")

    potential_scripts = list(search_root.rglob('run.sh'))
    if not potential_scripts:
        raise FileNotFoundError(f"致命錯誤：在 '{search_root}' 目錄下找不到任何 'run.sh' 部署腳本！")

    log_manager.log("INFO", f"找到 {len(potential_scripts)} 個可能的 run.sh。正在逐一驗證...")

    for script_path in potential_scripts:
        project_path = script_path.parent
        core_app_path = project_path / "integrated_platform" / "src" / "main.py"
        log_manager.log("INFO", f"正在測試路徑: {project_path} ... 檢查核心檔案: {core_app_path}")

        if core_app_path.is_file():
            log_manager.log("SUCCESS", f"驗證成功！專案路徑已鎖定: {project_path}")
            return project_path, script_path

    # 如果循環結束都沒有找到有效的路徑
    error_msg = "致命錯誤：已找到 run.sh，但找不到有效的專案結構。請確保 'run.sh' 與 'integrated_platform/src/main.py' 位於正確的相對位置。"
    log_manager.log("CRITICAL", error_msg)
    raise FileNotFoundError(error_msg)

# ==============================================================================
# SECTION 5: 即時日誌子程序執行器
# ==============================================================================
def run_subprocess_with_streaming_logs(command, cwd, env=None):
    """執行一個子程序，並將其 stdout 和 stderr 即時串流到 LogManager。"""
    global log_manager
    log_manager.log("INFO", f"準備在目錄 '{cwd}' 中執行指令: {' '.join(command)}")
    process = subprocess.Popen(
        command, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        text=True, encoding='utf-8', errors='replace', env=env or os.environ
    )
    for line in iter(process.stdout.readline, ''):
        log_manager.log("INFO", line.strip())
    process.stdout.close()
    return_code = process.wait()
    if return_code != 0:
        log_manager.log("ERROR", f"指令執行失敗，返回碼: {return_code}")
        raise subprocess.CalledProcessError(return_code, command)
    log_manager.log("SUCCESS", "指令執行成功。")
    return True

# ==============================================================================
# SECTION 6: 作戰主流程
# ==============================================================================
def main():
    global log_manager, display_thread, SQLITE_DB_PATH
    log_manager = None
    display_thread = None
    SQLITE_DB_PATH = None

    start_time_str = datetime.now(TAIPEI_TZ).strftime('%Y-%m-%d %H:%M:%S')

    try:
        temp_db_path = Path("/content/temp_logs.sqlite")
        if temp_db_path.exists(): temp_db_path.unlink()
        log_manager = LogManager(temp_db_path, version=APP_VERSION)
        log_manager.log("INFO", f"作戰流程開始 (版本 {APP_VERSION}，啟動於 {start_time_str})。")

        display_thread = DisplayManager(temp_db_path, LOG_DISPLAY_LINES, STATUS_REFRESH_INTERVAL, STOP_EVENT)
        display_thread.start()
        time.sleep(0.5)

        PROJECT_PATH, RUN_SCRIPT_PATH = find_project_path()

        SQLITE_DB_PATH = PROJECT_PATH / "logs.sqlite"
        if SQLITE_DB_PATH.exists(): SQLITE_DB_PATH.unlink()
        log_manager.db_path = SQLITE_DB_PATH
        log_manager._create_table()
        display_thread.db_path = SQLITE_DB_PATH
        log_manager.log("INFO", "日誌系統已切換至最終路徑。")

        env = os.environ.copy()
        env['LOG_DB_PATH'] = str(SQLITE_DB_PATH)
        env['UVICORN_PORT'] = str(FASTAPI_PORT)
        env['APP_VERSION'] = APP_VERSION

        run_subprocess_with_streaming_logs(command=["bash", str(RUN_SCRIPT_PATH)], cwd=PROJECT_PATH, env=env)
        create_public_portal(port=FASTAPI_PORT)
        log_manager.log("SUCCESS", f"作戰系統已上線！要停止所有服務，請點擊此儲存格的「中斷執行」(■) 按鈕。")
        while not STOP_EVENT.is_set():
            time.sleep(1)

    except (KeyboardInterrupt, subprocess.CalledProcessError) as e:
        if isinstance(e, subprocess.CalledProcessError):
            log_manager.log("CRITICAL", "後端部署失敗，請檢查上方日誌以了解詳細原因。")
        else:
            log_manager.log("INFO", "\n[偵測到使用者手動中斷請求...]")
    except Exception as e:
        if log_manager:
            log_manager.log("CRITICAL", f"作戰流程發生未預期的嚴重錯誤: {e}")
            log_manager.log("CRITICAL", traceback.format_exc())
        print(f"\n💥 作戰流程發生未預期的嚴重錯誤，系統即將終止。")
        traceback.print_exc()
        time.sleep(1)
    finally:
        end_time_str = datetime.now(TAIPEI_TZ).strftime('%Y-%m-%d %H:%M:%S')
        if log_manager:
            log_manager.log("INFO", f"作戰流程結束 (結束於 {end_time_str})。")
            log_manager.log("INFO", "[正在執行終端清理與日誌歸檔程序...]")
            archive_final_log(SQLITE_DB_PATH)
            log_manager.log("SUCCESS", "部署流程已結束，所有服務已安全關閉。")
        STOP_EVENT.set()
        if display_thread:
            display_thread.join(timeout=2)

if __name__ == "__main__":
    main()
