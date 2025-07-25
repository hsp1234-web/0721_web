# ==============================================================================
#                      鳳凰之心 Colab 橋接器 (v15.0)
#
#   本腳本為在 Google Colab 環境中執行後端應用的核心。
#   它被設計為由一個極簡的 Colab 儲存格觸發，接收參數後，
#   負責處理所有複雜的任務，包括：
#   - 動態 UI 渲染與日誌顯示
#   - 安全的進程管理與生命週期控制
#   - 動態路徑發現，避免硬編碼
#   - 錯誤處理與最終日誌歸檔
#
# ==============================================================================

# --- 標準函式庫 ---
import os
import sys
import subprocess
import threading
import time
import sqlite3
import psutil
import traceback
import html
import uuid
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# --- Colab 專用模組 ---
try:
    from IPython.display import display, HTML, Javascript, clear_output
    from google.colab import output as colab_output
except ImportError:
    print("警告：未能導入 Colab 專用模組。此腳本可能無法在非 Colab 環境中正確顯示 UI。")
    # 提供備用方案，以防在本地環境執行
    class DummyDisplay:
        def display(self, *args, **kwargs): pass
        def HTML(self, *args, **kwargs): pass
        def Javascript(self, *args, **kwargs): pass
        def clear_output(self, *args, **kwargs): pass
    display = HTML = Javascript = clear_output = DummyDisplay()
    class DummyColabOutput:
        def redirect_to_element(self, *args, **kwargs): return self
        def clear(self): pass
        def serve_kernel_port_as_iframe(self, *args, **kwargs): pass
        def __enter__(self): pass
        def __exit__(self, *args): pass
    colab_output = DummyColabOutput()

# ==============================================================================
# SECTION 0: 動態路徑與全域設定
# ==============================================================================
# 以此腳本自身位置為錨點，動態計算所有路徑
try:
    SCRIPT_PATH = Path(__file__).resolve()
    PROJECT_ROOT = SCRIPT_PATH.parent
except NameError:
    # 如果在非標準執行環境（如某些 Notebook）中 __file__ 未定義，則使用當前工作目錄
    PROJECT_ROOT = Path(os.getcwd()).resolve()

TAIPEI_TZ = ZoneInfo("Asia/Taipei")
STOP_EVENT = threading.Event()
SERVER_PROCESS = None
UI_INSTANCE_ID = f"phoenix-ui-{uuid.uuid4().hex[:8]}"

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
            try:
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
            except Exception as e:
                print(f"CRITICAL DB TABLE CREATION ERROR: {e}", file=sys.stderr)

    def log(self, level, message):
        ts = datetime.now(TAIPEI_TZ).isoformat()
        with self.lock:
            try:
                with self._get_connection() as conn:
                    conn.execute("INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?);", (ts, level, message))
                    conn.commit()
            except Exception as e:
                print(f"CRITICAL DB LOGGING ERROR: {e}", file=sys.stderr)

# ==============================================================================
# SECTION 2: 智慧顯示管理器
# ==============================================================================
class DisplayManager(threading.Thread):
    """在獨立執行緒中，作為唯一的「畫家」，持續從資料庫讀取日誌並更新前端UI。"""
    def __init__(self, db_path, display_lines, refresh_interval, stop_event, ui_instance_id):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.display_lines = max(1, display_lines)
        self.refresh_interval = max(0.1, refresh_interval)
        self.stop_event = stop_event
        self.ui_instance_id = ui_instance_id
        self.last_log_id = 0
        self.last_status_update = 0

    def _execute_js(self, js_code):
        try:
            display(Javascript(js_code))
        except Exception as e:
            pass

    def setup_ui(self):
        self._execute_js("document.querySelectorAll('.phoenix-command-center').forEach(el => el.remove());")
        time.sleep(0.1)
        clear_output(wait=True)
        ui_html = f"""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Fira+Code&family=Noto+Sans+TC&display=swap');
            .phoenix-container {{ font-family: 'Noto Sans TC', 'Fira Code', 'Consolas', monospace; font-size: 14px; line-height: 1.6; color: #E0E0E0; }}
            .phoenix-grid-container {{ display: grid; grid-template-columns: 10ch 11ch 1fr; gap: 0 12px; align-items: baseline; }}
            .phoenix-grid-item {{ white-space: pre-wrap; word-break: break-all; }}
            #log-panel-container-{{self.ui_instance_id}} {{ height: 45vh; overflow-y: auto; border: 1px solid #555; padding: 12px; background-color: #263238; display: flex; flex-direction: column-reverse; border-radius: 8px; }}
            #status-bar-{{self.ui_instance_id}} {{ margin-top: 8px; padding: 6px 12px; border: 1px solid #555; background-color: #37474F; border-radius: 8px; }}
            #bottom-panel-container-{{self.ui_instance_id}} {{ height: calc(55vh - 70px); margin-top: 8px; border: 1px solid #555; border-radius: 8px; overflow: hidden; background-color: #1E1F20; }}
        </style>
        <div id="{self.ui_instance_id}" class="phoenix-command-center phoenix-container">
            <div id="log-panel-container-{{self.ui_instance_id}}"><div id="log-panel-{{self.ui_instance_id}}" class="phoenix-grid-container"></div></div>
            <div id="status-bar-{{self.ui_instance_id}}" class="phoenix-grid-container"></div>
            <div id="bottom-panel-container-{{self.ui_instance_id}}"><p style="padding:20px; color:#999;">正在初始化指揮中心，請稍候...</p></div>
        </div>
        """
        display(HTML(ui_html))

    def _update_status_bar(self):
        now = time.time()
        if now - self.last_status_update < self.refresh_interval: return
        self.last_status_update = now
        try:
            cpu, ram = psutil.cpu_percent(), psutil.virtual_memory().percent
            time_str = datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')
            status_html = (f"<div class='phoenix-grid-item' style='color: #CFD8DC;'>{time_str}</div>"
                           f"<div class='phoenix-grid-item' style='color: #CFD8DC;'>CPU: {cpu:4.1f}%</div>"
                           f"<div class='phoenix-grid-item' style='color: #4CAF50; font-weight:bold;'>RAM: {ram:4.1f}% | 系統運行中</div>")
            escaped_status_html = status_html.replace('`', '\\`')
            js_code = f"const sb = document.getElementById('status-bar-{self.ui_instance_id}'); if (sb) sb.innerHTML = `{escaped_status_html}`;"
            self._execute_js(js_code)
        except Exception: pass

    def _update_log_panel(self):
        if not self.db_path or not self.db_path.exists(): return
        try:
            with sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True) as conn:
                new_logs = conn.execute("SELECT id, timestamp, level, message FROM logs WHERE id > ? ORDER BY id ASC", (self.last_log_id,)).fetchall()
            if not new_logs: return
            log_html_batch = ""
            for log_id, ts, level, msg in new_logs:
                formatted_ts = datetime.fromisoformat(ts).strftime('%H:%M:%S')
                level_upper = level.upper()
                colors = {"SUCCESS": '#81C784', "ERROR": '#E57373', "CRITICAL": '#EF5350', "WARNING": '#FFB74D', "BATTLE": '#64B5F6', "INFO": '#90A4AE'}
                level_color = colors.get(level_upper, '#B0BEC5')
                escaped_msg = html.escape(msg)
                log_html_batch += (f"<div class='phoenix-grid-item' style='color: #B0BEC5;'>[{formatted_ts}]</div>"
                                   f"<div class='phoenix-grid-item' style='color: {level_color}; font-weight: bold;'>[{level_upper:^8}]</div>"
                                   f"<div class='phoenix-grid-item'>{escaped_msg}</div>")
                self.last_log_id = log_id
            escaped_log_html_batch = log_html_batch.replace('`', '\\`')
            js_code = f"""
            const p = document.getElementById('log-panel-{self.ui_instance_id}');
            if (p) {{
                const c = document.createElement('div'); c.style.display = 'contents'; c.innerHTML = `{escaped_log_html_batch}`;
                p.prepend(...c.children);
                while (p.childElementCount > ({self.display_lines} * 3)) {{ for(let i=0; i<3; i++) p.removeChild(p.lastChild); }}
            }}"""
            self._execute_js(js_code)
        except Exception: pass

    def run(self):
        self.setup_ui()
        while not self.stop_event.is_set():
            self._update_status_bar()
            self._update_log_panel()
            time.sleep(0.2)

# ==============================================================================
# SECTION 3: 核心輔助函式
# ==============================================================================
def execute_and_stream(cmd, cwd, log_manager):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace', cwd=cwd, bufsize=1
    )
    def stream_logger(stream, level):
        try:
            for line in iter(stream.readline, ''):
                if line:
                    log_manager.log(level, line.strip())
        finally:
            stream.close()
    threading.Thread(target=stream_logger, args=(process.stdout, "INFO"), daemon=True).start()
    threading.Thread(target=stream_logger, args=(process.stderr, "ERROR"), daemon=True).start()
    return process

def create_public_portal(port, log_manager, ui_instance_id):
    log_manager.log("BATTLE", f"正在將應用程式嵌入至指揮中心 (埠號: {port})...")
    panel_id = f'#bottom-panel-container-{ui_instance_id}'
    try:
        with colab_output.redirect_to_element(panel_id):
            colab_output.clear()
            colab_output.serve_kernel_port_as_iframe(port, width='100%', height='100%')
        log_manager.log("SUCCESS", "互動指揮中心已成功嵌入。")
    except Exception as e:
        log_manager.log("CRITICAL", f"嵌入互動指揮中心失敗: {e}")

def archive_final_log(db_path, archive_dir, log_manager):
    log_manager.log("INFO", "正在生成最終作戰報告...")
    if not db_path or not db_path.is_file():
        log_manager.log("WARNING", f"找不到日誌資料庫 ({db_path})，無法歸檔。")
        return
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        archive_filename = f"作戰日誌_{datetime.now(TAIPEI_TZ).strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        archive_filepath = archive_dir / archive_filename
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            logs = conn.execute("SELECT timestamp, level, message FROM logs ORDER BY id ASC").fetchall()
        with open(archive_filepath, 'w', encoding='utf-8') as f:
            f.write(f"--- 鳳凰之心作戰日誌 v15.0 ---\n")
            f.write(f"報告生成時間: {datetime.now(TAIPEI_TZ).isoformat()}\n")
            f.write("--------------------------------------------------\n\n")
            for ts, lvl, msg in logs:
                f.write(f"[{ts}] [{lvl.upper():<8}] {msg}\n")
        log_manager.log("SUCCESS", f"完整日誌已歸檔至: {archive_filepath}")

        # --- 新增的複製步驟 ---
        try:
            import shutil
            destination_dir = Path("/content") / archive_dir.name
            if destination_dir.exists():
                shutil.rmtree(destination_dir)
            shutil.copytree(archive_dir, destination_dir)
            log_manager.log("SUCCESS", f"日誌副本已成功建立於根目錄: {destination_dir}")
        except Exception as copy_e:
            log_manager.log("ERROR", f"複製日誌到根目錄時失敗: {copy_e}")

    except Exception as e:
        log_manager.log("ERROR", f"歸檔日誌時發生錯誤: {e}")
        log_manager.log("ERROR", traceback.format_exc())

# ==============================================================================
# SECTION 4: 作戰主流程 (進入點)
# ==============================================================================
def main(config: dict):
    """
    Colab 橋接器的主要進入點函式。
    接收來自 Colab 儲存格的設定，並執行完整的後端啟動與監控流程。
    """
    global SERVER_PROCESS, STOP_EVENT, UI_INSTANCE_ID

    log_manager = None
    display_thread = None
    sqlite_db_path = None

    try:
        # 步驟 1: 解構設定並啟動臨時日誌
        log_display_lines = config.get("log_display_lines", 100)
        status_refresh_interval = config.get("status_refresh_interval", 0.5)
        archive_folder_name = config.get("archive_folder_name", "作戰日誌歸檔")
        fastapi_port = config.get("fastapi_port", 8000)

        temp_db_path = PROJECT_ROOT / f"temp_logs_{uuid.uuid4().hex[:8]}.sqlite"
        log_manager = LogManager(temp_db_path)
        display_thread = DisplayManager(temp_db_path, log_display_lines, status_refresh_interval, STOP_EVENT, UI_INSTANCE_ID)
        display_thread.start()
        time.sleep(0.5)

        # 步驟 2: 驗證路徑並切換到最終日誌
        log_manager.log("INFO", f"專案根目錄 (動態偵測): {PROJECT_ROOT}")
        sqlite_db_path = PROJECT_ROOT / "logs.sqlite"
        if sqlite_db_path.exists():
            log_manager.log("WARNING", f"發現舊的日誌資料庫，將其刪除: {sqlite_db_path}")
            sqlite_db_path.unlink()
        log_manager.log("INFO", f"日誌資料庫將建立於: {sqlite_db_path}")
        log_manager.db_path = sqlite_db_path
        log_manager._create_table()
        display_thread.db_path = sqlite_db_path

        # 步驟 3: 執行依賴安裝 (假設 uv_manager.py 存在)
        log_manager.log("BATTLE", "作戰流程啟動：正在安裝/驗證專案依賴...")
        # 檢查 uv_manager.py 是否存在
        uv_manager_path = PROJECT_ROOT / "uv_manager.py"
        if not uv_manager_path.is_file():
            # 如果不存在，則執行備用方案：直接安裝 requirements.txt
            log_manager.log("WARNING", "未找到 'uv_manager.py'，將執行備用安裝流程。")
            log_manager.log("INFO", "正在安裝 'uv' 工具...")
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True, capture_output=True, text=True)
            log_manager.log("INFO", "正在使用 'uv' 安裝 'requirements.txt'...")
            install_process = execute_and_stream(["uv", "pip", "install", "-r", "requirements.txt"], PROJECT_ROOT, log_manager)
        else:
            install_process = execute_and_stream([sys.executable, "uv_manager.py"], PROJECT_ROOT, log_manager)

        install_process.wait()
        if install_process.returncode != 0:
            raise RuntimeError("依賴安裝失敗，請檢查日誌輸出以了解詳細原因。作戰終止。")
        log_manager.log("SUCCESS", "專案依賴已成功配置。")


        # 步驟 4: 啟動主應用伺服器
        log_manager.log("BATTLE", "正在啟動主應用伺服器...")
        SERVER_PROCESS = execute_and_stream(
            [sys.executable, "run.py", "--port", str(fastapi_port), "--host", "0.0.0.0"],
            PROJECT_ROOT, log_manager
        )

        # 步驟 5: 嵌入介面並進入監控模式
        log_manager.log("INFO", "等待 10 秒以確保伺服器完全啟動...")
        time.sleep(10)
        create_public_portal(fastapi_port, log_manager, UI_INSTANCE_ID)

        log_manager.log("SUCCESS", "作戰系統已上線！要停止所有服務並歸檔日誌，請點擊此儲存格的「中斷執行」(■) 按鈕。")

        while SERVER_PROCESS.poll() is None:
            if STOP_EVENT.is_set():
                break
            time.sleep(1)

        if SERVER_PROCESS.poll() is not None and SERVER_PROCESS.returncode != 0:
            log_manager.log("CRITICAL", f"後端進程意外終止，返回碼: {SERVER_PROCESS.returncode}")

    except KeyboardInterrupt:
        if log_manager:
            log_manager.log("WARNING", "\n[偵測到使用者手動中斷請求...正在準備安全關閉...]")
    except Exception as e:
        error_message = f"💥 作戰流程發生未預期的嚴重錯誤: {e}"
        print(f"\n{error_message}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        if log_manager:
            log_manager.log("CRITICAL", error_message)
            log_manager.log("CRITICAL", traceback.format_exc())
            time.sleep(1)
    finally:
        # 步驟 6: 終端清理與日誌歸檔
        STOP_EVENT.set()
        if log_manager:
            log_manager.log("BATTLE", "[正在執行終端清理程序...]")

        if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
            log_manager.log("INFO", f"正在終止後端伺服器進程 (PID: {SERVER_PROCESS.pid})...")
            SERVER_PROCESS.terminate()
            try:
                SERVER_PROCESS.wait(timeout=5)
                log_manager.log("SUCCESS", "後端伺服器已成功終止。")
            except subprocess.TimeoutExpired:
                log_manager.log("WARNING", "後端伺服器未能溫和終止，將強制結束。")
                SERVER_PROCESS.kill()

        if display_thread and display_thread.is_alive():
            display_thread.join(timeout=2)

        if log_manager and sqlite_db_path:
            archive_dir = PROJECT_ROOT / archive_folder_name
            archive_final_log(sqlite_db_path, archive_dir, log_manager)
        else:
            if log_manager:
                log_manager.log("ERROR", "無法歸檔日誌，因為最終資料庫路徑未能成功設定。")

        if log_manager:
            log_manager.log("SUCCESS", "部署流程已結束，所有服務已安全關閉。")

        print("\n--- 系統已安全關閉 ---")
        if 'temp_db_path' in locals() and temp_db_path.exists():
            try:
                temp_db_path.unlink()
            except Exception:
                pass
