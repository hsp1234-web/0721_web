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
    # 提供備用方案，以防在本地環境執行
    class DummyDisplay:
        def display(self, *args, **kwargs): pass
        def HTML(self, *args, **kwargs): pass
        def Javascript(self, *args, **kwargs): pass
        # 讓 clear_output 成為一個可呼叫的物件，即使它什麼都不做
        def clear_output(self, wait=False): pass

    dummy_display_instance = DummyDisplay()
    display = dummy_display_instance.display
    HTML = dummy_display_instance.HTML
    Javascript = dummy_display_instance.Javascript
    clear_output = dummy_display_instance.clear_output
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
# SECTION 2: 精準指示器 (Precision Indicator)
# ==============================================================================
import collections

class PrecisionIndicator:
    """
    v82.0 精準指示器介面。
    採用雙區塊、分離刷新策略，提供高效且無閃爍的終端監控體驗。
    - 高頻區 (Live Indicator): 即時顯示系統狀態，快速更新。
    - 低頻區 (Situation Report): 僅在出現關鍵日誌時刷新，減少資源消耗。
    """
    def __init__(self, log_manager, stats_dict):
        """
        初始化指示器。
        :param log_manager: 後端日誌管理器實例。
        :param stats_dict: 一個共享的字典，用於跨執行緒傳遞即時狀態。
        """
        self.log_manager = log_manager
        self.stats_dict = stats_dict
        self.stop_event = threading.Event()
        self.render_thread = threading.Thread(target=self._run, daemon=True)
        # 使用 deque 作為日誌緩衝區，設定最大長度
        self.log_deque = collections.deque(maxlen=50)

    def start(self):
        """啟動背景渲染執行緒。"""
        self.render_thread.start()

    def stop(self):
        """設置停止事件並等待執行緒安全退出。"""
        self.stop_event.set()
        self.render_thread.join()

    KEY_LOG_LEVELS = {"SUCCESS", "ERROR", "CRITICAL", "BATTLE", "WARNING"}

    def log(self, level, message):
        """
        接收新的日誌訊息。
        所有日誌都無條件傳遞給後端儲存，但只有關鍵日誌會觸發 UI 重繪。
        """
        # 步驟 1: 無條件寫入後端日誌，這是記錄的真相來源
        self.log_manager.log(level, message)

        # 步驟 2: 判斷是否為關鍵日誌，以決定是否更新 UI
        if level.upper() in self.KEY_LOG_LEVELS:
            # 獲取當前時間
            timestamp = datetime.now(TAIPEI_TZ)
            # 將日誌元組存入 deque
            self.log_deque.append((timestamp, level, message))
            # 觸發近況彙報區的重繪
            self._render_situation_report()

    def _render_situation_report(self):
        """
        低頻渲染函式：重繪整個「近況彙報」區。
        此函式成本較高，只應在收到關鍵日誌時呼叫。
        """
        # 1. 清除 Colab 儲存格的輸出
        # wait=True 確保在繪製新內容前，舊內容已完全清除，避免閃爍
        clear_output(wait=True)

        # 2. 定義日誌等級的顏色
        colors = {
            "SUCCESS": "\x1b[32m",  # 綠色
            "ERROR": "\x1b[31m",    # 紅色
            "CRITICAL": "\x1b[91m", # 亮紅色
            "WARNING": "\x1b[33m",  # 黃色
            "BATTLE": "\x1b[34m",   # 藍色
            "INFO": "\x1b[37m",     # 白色
            "DEFAULT": "\x1b[0m"    # 重設
        }

        # 3. 遍歷 deque 中的所有日誌並打印
        for timestamp, level, message in self.log_deque:
            color = colors.get(level.upper(), colors["INFO"])
            reset_color = colors["DEFAULT"]

            ts_str = timestamp.strftime('%H:%M:%S')
            level_str = f"[{level.upper():^8}]"

            print(f"\x1b[90m{ts_str}{reset_color} {color}{level_str}{reset_color} {message}")

        # 4. 重新打印一次即時狀態行，因為 clear_output 會清除所有東西
        self._render_live_indicator()

    def _render_live_indicator(self):
        """
        高頻渲染函式：更新即時狀態行。
        使用 ANSI 跳脫字元 `\\r` (歸位) 和 `\\033[K` (清除到行尾)
        來實現單行無閃爍刷新。
        """
        try:
            # 從共享字典中獲取最新狀態，如果沒有則使用預設值
            cpu = self.stats_dict.get('cpu', 'N/A')
            ram = self.stats_dict.get('ram', 'N/A')
            progress_label = self.stats_dict.get('progress_label', '初始化中...')

            # 準備要顯示的各部分
            time_str = datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')

            # 組合最終的單行字串
            # \033[K 清除從游標到行尾的內容，確保舊的較長字串不會殘留
            indicator_line = f"\r\033[K  \x1b[36m[狀態]\x1b[0m {time_str} | \x1b[33mCPU:\x1b[0m {cpu:5.1f}% | \x1b[33mRAM:\x1b[0m {ram:5.1f}% | \x1b[32m{progress_label}\x1b[0m"

            # 使用 sys.stdout.write 以獲得更好的控制
            sys.stdout.write(indicator_line)
            sys.stdout.flush()

        except Exception as e:
            # 在開發過程中，如果渲染出錯，打印錯誤但不要讓執行緒崩潰
            # print(f"\n[INDICATOR RENDER ERROR] {e}\n")
            pass

    def _run(self):
        """背景執行緒的主迴圈，負責高頻渲染。"""
        while not self.stop_event.is_set():
            self._render_live_indicator()
            time.sleep(0.2)

# ==============================================================================
# SECTION 3: 核心輔助函式
# ==============================================================================
def execute_and_stream(cmd, cwd, system_log):
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding='utf-8', errors='replace', cwd=cwd, bufsize=1
    )
    def stream_logger(stream, level):
        try:
            for line in iter(stream.readline, ''):
                if line:
                    system_log(level, line.strip())
        finally:
            stream.close()
    threading.Thread(target=stream_logger, args=(process.stdout, "INFO"), daemon=True).start()
    threading.Thread(target=stream_logger, args=(process.stderr, "ERROR"), daemon=True).start()
    return process

def create_public_portal(port, system_log, ui_instance_id):
    system_log("BATTLE", f"正在將應用程式嵌入至指揮中心 (埠號: {port})...")
    panel_id = f'#bottom-panel-container-{ui_instance_id}'
    try:
        # 這段 HTML 和 JS 程式碼是為了在 Colab 中建立一個視覺化的 UI 容器
        # 我們將 FastAPI 應用程式嵌入到這個容器的下半部分。
        ui_html = f"""
        <style>
            /* 這裡可以添加一些基本的 CSS 來美化框架 */
            .phoenix-main-container {{ height: 80vh; display: flex; flex-direction: column; }}
            #situation-report-{{ui_instance_id}} {{ flex: 1; overflow-y: auto; padding: 10px; background-color: #1E1E1E; border-radius: 8px; border: 1px solid #444; font-family: 'Fira Code', monospace; }}
            #live-indicator-{{ui_instance_id}} {{ padding: 5px 10px; background-color: #333; border-top: 1px solid #444; font-family: 'Fira Code', monospace; }}
            #bottom-panel-container-{{ui_instance_id}} {{ height: 40vh; margin-top: 8px; border: 1px solid #555; border-radius: 8px; overflow: hidden; background-color: #1E1F20; }}
        </style>
        <div id="phoenix-main-container-{{ui_instance_id}}" class="phoenix-main-container">
            <div id="situation-report-{{ui_instance_id}}"></div>
            <div id="live-indicator-{{ui_instance_id}}"></div>
            <div id="bottom-panel-container-{{ui_instance_id}}"><p style="padding:20px; color:#999;">正在等待應用程式嵌入...</p></div>
        </div>
        """
        display(HTML(ui_html))
        time.sleep(0.5) # 等待 DOM 更新

        with colab_output.redirect_to_element(panel_id):
            colab_output.clear()
            colab_output.serve_kernel_port_as_iframe(port, width='100%', height='100%')
        system_log("SUCCESS", "互動指揮中心已成功嵌入。")
    except Exception as e:
        system_log("CRITICAL", f"嵌入互動指揮中心失敗: {e}")

def archive_final_log(db_path, archive_dir, log_manager):
    # 歸檔函式保持不變，直接使用 log_manager
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
    indicator = None
    sqlite_db_path = None
    stats_dict = {} # 用於跨執行緒共享狀態

    try:
        # 步驟 1: 解構設定並啟動日誌與指示器
        archive_folder_name = config.get("archive_folder_name", "作戰日誌歸檔")
        fastapi_port = config.get("fastapi_port", 8000)

        # 由於 PrecisionIndicator 直接處理日誌，不再需要臨時資料庫
        sqlite_db_path = PROJECT_ROOT / "logs.sqlite"
        if sqlite_db_path.exists():
            # 確保一個乾淨的開始
            sqlite_db_path.unlink()

        log_manager = LogManager(sqlite_db_path)
        indicator = PrecisionIndicator(log_manager=log_manager, stats_dict=stats_dict)

        # 將 indicator 的 log 方法作為系統的主要日誌點
        # 這樣所有日誌都會先經過 indicator 再存入資料庫
        system_log = indicator.log

        indicator.start()

        # 步驟 2: 驗證路徑
        system_log("INFO", f"專案根目錄 (動態偵測): {PROJECT_ROOT}")
        system_log("INFO", f"日誌資料庫將建立於: {sqlite_db_path}")

        # 步驟 3: 執行依賴安裝
        system_log("BATTLE", "作戰流程啟動：正在安裝/驗證專案依賴...")
        uv_manager_path = PROJECT_ROOT / "uv_manager.py"
        if not uv_manager_path.is_file():
            system_log("WARNING", "未找到 'uv_manager.py'，將執行備用安裝流程。")
            system_log("INFO", "正在安裝 'uv' 工具...")
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True, capture_output=True, text=True)
            system_log("INFO", "正在使用 'uv' 安裝 'requirements.txt'...")
            install_process = execute_and_stream(["uv", "pip", "install", "-r", "requirements.txt"], PROJECT_ROOT, system_log)
        else:
            install_process = execute_and_stream([sys.executable, "uv_manager.py"], PROJECT_ROOT, system_log)

        install_process.wait()
        if install_process.returncode != 0:
            raise RuntimeError("依賴安裝失敗，請檢查日誌輸出以了解詳細原因。作戰終止。")
        system_log("SUCCESS", "專案依賴已成功配置。")

        # 步驟 4: 啟動主應用伺服器
        system_log("BATTLE", "正在啟動主應用伺服器...")
        SERVER_PROCESS = execute_and_stream(
            [sys.executable, "run.py", "--port", str(fastapi_port), "--host", "0.0.0.0"],
            PROJECT_ROOT, system_log
        )

        # 步驟 5: 嵌入介面並進入監控模式
        system_log("INFO", "等待 10 秒以確保伺服器完全啟動...")
        time.sleep(10)
        create_public_portal(fastapi_port, system_log, UI_INSTANCE_ID)

        system_log("SUCCESS", "作戰系統已上線！要停止所有服務並歸檔日誌，請點擊此儲存格的「中斷執行」(■) 按鈕。")

        # 進入主監控迴圈
        while SERVER_PROCESS.poll() is None:
            if STOP_EVENT.is_set():
                break

            # 更新共享狀態字典，供 PrecisionIndicator 使用
            try:
                stats_dict['cpu'] = psutil.cpu_percent()
                stats_dict['ram'] = psutil.virtual_memory().percent
                # 這裡可以根據應用程式的具體邏輯更新 progress_label
                # 例如，我們可以從一個共享佇列或檔案中讀取進度
                stats_dict.setdefault('progress_label', '系統運行中')
            except psutil.Error:
                stats_dict['cpu'] = -1.0
                stats_dict['ram'] = -1.0

            time.sleep(1) # 主執行緒不需要太頻繁地更新

        if SERVER_PROCESS.poll() is not None and SERVER_PROCESS.returncode != 0:
            system_log("CRITICAL", f"後端進程意外終止，返回碼: {SERVER_PROCESS.returncode}")

    except KeyboardInterrupt:
        if 'system_log' in locals():
            system_log("WARNING", "\n[偵測到使用者手動中斷請求...正在準備安全關閉...]")
    except Exception as e:
        error_message = f"💥 作戰流程發生未預期的嚴重錯誤: {e}"
        print(f"\n{error_message}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        if 'system_log' in locals():
            system_log("CRITICAL", error_message)
            system_log("CRITICAL", traceback.format_exc())
            time.sleep(1)
    finally:
        # 步驟 6: 終端清理與日誌歸檔
        STOP_EVENT.set()
        if 'system_log' in locals():
            system_log("BATTLE", "[正在執行終端清理程序...]")

        if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
            # 此處的日誌也應該通過 system_log
            system_log("INFO", f"正在終止後端伺服器進程 (PID: {SERVER_PROCESS.pid})...")
            SERVER_PROCESS.terminate()
            try:
                SERVER_PROCESS.wait(timeout=5)
                system_log("SUCCESS", "後端伺服器已成功終止。")
            except subprocess.TimeoutExpired:
                system_log("WARNING", "後端伺服器未能溫和終止，將強制結束。")
                SERVER_PROCESS.kill()

        if indicator:
            indicator.stop()

        if log_manager and sqlite_db_path:
            archive_dir = PROJECT_ROOT / archive_folder_name
            # 注意：這裡我們仍然使用原始的 log_manager 進行歸檔，而不是 indicator 的 log 方法
            # 因為歸檔操作本身不應該觸發 UI 更新。
            archive_final_log(sqlite_db_path, archive_dir, log_manager)
        elif 'system_log' in locals():
            # 如果 log_manager 因故不存在，但 system_log 存在，至少要發出一個警告
            system_log("ERROR", "無法歸檔日誌，因為最終資料庫路徑未能成功設定。")

        if 'system_log' in locals():
             system_log("SUCCESS", "部署流程已結束，所有服務已安全關閉。")

        print("\n--- 系統已安全關閉 ---")
