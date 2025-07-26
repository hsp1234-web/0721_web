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
import sqlite3
import subprocess
import sys
import threading
import time
import traceback
import uuid
from datetime import datetime
from pathlib import Path

import psutil
from zoneinfo import ZoneInfo
import collections

# --- Colab 專用模組 ---
try:
    from google.colab import output as colab_output
    from IPython.display import HTML, Javascript, clear_output, display
except ImportError:
    print("警告：未能導入 Colab 專用模組。此腳本可能無法在非 Colab 環境中正確顯示 UI。")
    # 提供備用方案，以防在本地環境執行
    class DummyDisplay:
        def display(self, *args, **kwargs): pass
        def html(self, *args, **kwargs): pass
        def javascript(self, *args, **kwargs): pass
        # 讓 clear_output 成為一個可呼叫的物件，即使它什麼都不做
        def clear_output(self, wait=False): pass

    dummy_display_instance = DummyDisplay()
    display = dummy_display_instance.display
    HTML = dummy_display_instance.html
    Javascript = dummy_display_instance.javascript
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
                    conn.execute(
                        "INSERT INTO logs (timestamp, level, message) VALUES (?, ?, ?);",
                        (ts, level, message)
                    )
                    conn.commit()
            except Exception as e:
                print(f"CRITICAL DB LOGGING ERROR: {e}", file=sys.stderr)

# ==============================================================================
# SECTION 2: 精準指示器 (Precision Indicator)
# ==============================================================================
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
        self.activated = threading.Event() # 新增的啟動事件
        self.render_thread = threading.Thread(target=self._run, daemon=True)
        # 使用 deque 作為日誌緩衝區，設定最大長度
        self.log_deque = collections.deque(maxlen=50)

    def start(self):
        """啟動背景渲染執行緒。"""
        self.render_thread.start()

    def activate(self):
        """活化渲染迴圈，允許其開始繪製。"""
        self.activated.set()

    def stop(self):
        """設置停止事件並等待執行緒安全退出。"""
        self.stop_event.set()
        self.render_thread.join()

    # 將 INFO 也視為關鍵日誌，以便在儀表板上顯示啟動過程
    KEY_LOG_LEVELS = {"SUCCESS", "ERROR", "CRITICAL", "BATTLE", "WARNING", "INFO"}

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
            # 將日誌元組存入 deque，供下一次渲染使用
            self.log_deque.append((timestamp, level, message))

    def _create_progress_bar(self, percentage, length=10):
        """根據百分比生成一個文字進度條。"""
        filled_length = int(length * percentage / 100)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"[{bar}] {percentage:5.1f}%"

    def _render_top_panel(self):
        """渲染儀表板的頂部面板，包含資源監控和服務狀態。"""
        cpu_perc = self.stats_dict.get('cpu', 0.0)
        ram_perc = self.stats_dict.get('ram', 0.0)
        fastapi_status = self.stats_dict.get('fastapi_status', '⏳')
        websocket_status = self.stats_dict.get('websocket_status', '⏳')
        db_status = self.stats_dict.get('db_status', '⏳')
        db_latency = self.stats_dict.get('db_latency', 'N/A')

        cpu_bar = self._create_progress_bar(cpu_perc)
        ram_bar = self._create_progress_bar(ram_perc)

        line1 = "│┌─ ⚙️ 即時資源監控 ───────────┐ ┌─ 🌐 核心服務狀態 ───────────┐│"
        line2 = f"││ CPU: {cpu_bar}   │ │ {fastapi_status} 後端 FastAPI 引擎        ││"
        line3 = f"││ RAM: {ram_bar}   │ │ {websocket_status} WebSocket 通訊頻道       ││"
        line4 = (f"││                           │ │ {db_status} 日誌資料庫 "
                 f"(延遲: {db_latency: <5}) ││")
        line5 = "│└───────────────────────────┘ └───────────────────────────┘│"
        header = ("┌" + "─" * 35 + " 鳳凰之心 v14.0 駕駛艙 " + "─" * 35 + "┐")

        return "\n".join([header, line1, line2, line3, line4, line5])

    def _render_log_panel(self):
        """渲染儀表板的日誌面板。"""
        header = "├" + "─" * 30 + " 近況彙報 (最新 5 條) " + "─" * 30 + "┤"
        log_styles = {
            "SUCCESS": ("\x1b[32m", "✅"), "ERROR": ("\x1b[31m", "🔴"),
            "CRITICAL": ("\x1b[91m", "🔥"), "WARNING": ("\x1b[33m", "🟡"),
            "BATTLE": ("\x1b[34m", "⚡"), "INFO": ("\x1b[37m", "✨"),
            "DEFAULT": ("\x1b[0m", "🔹")
        }
        lines = []
        num_logs = 5
        recent_logs = list(self.log_deque)[-num_logs:]

        for i in range(num_logs):
            if i < len(recent_logs):
                timestamp, level, message = recent_logs[i]
                color, icon = log_styles.get(level.upper(), log_styles["DEFAULT"])
                reset_color = log_styles["DEFAULT"][0]
                ts_str = timestamp.strftime('%H:%M:%S')
                level_str = f"[{level.upper():^7}]"
                max_msg_len = 58
                if len(message) > max_msg_len:
                    message_str = message[:max_msg_len] + '...'
                else:
                    message_str = message
                line = (f"│[{ts_str}] {color}{level_str}{reset_color} {icon} "
                        f"{message_str:<61}│")
                lines.append(line)
            else:
                lines.append("│" + " " * 78 + "│")

        footer = "└" + "─" * 78 + "┘"
        return "\n".join([header] + lines + [footer])

    def _render_status_bar(self):
        """渲染儀表板底部的狀態欄。"""
        bg_color = "\x1b[44m"
        reset = "\x1b[0m"
        cpu_perc = self.stats_dict.get('cpu', 0.0)
        ram_perc = self.stats_dict.get('ram', 0.0)
        system_status = self.stats_dict.get('system_status', '系統狀態未知')
        time_str = datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')
        status_line = (f" CPU: {cpu_perc:5.1f}% | RAM: {ram_perc:5.1f}% | "
                       f"{system_status} | {time_str} ")
        padded_line = status_line.ljust(80)
        return f"{bg_color}{padded_line}{reset}"

    def _run(self):
        """
        背景渲染執行緒的主迴圈。
        負責以固定頻率重繪整個儀表板。
        """
        self.activated.wait()
        while not self.stop_event.is_set():
            try:
                clear_output(wait=True)
                top_panel = self._render_top_panel()
                log_panel = self._render_log_panel()
                status_bar = self._render_status_bar()
                full_screen = f"{top_panel}\n{log_panel}\n{status_bar}"
                print(full_screen, end="", flush=True)
            except Exception as e:
                print(f"儀表板渲染錯誤: {e}")
            time.sleep(0.2)

# ==============================================================================
# SECTION 3: 核心輔助函式
# ==============================================================================
def execute_and_stream(cmd, cwd, system_log):
    env = os.environ.copy()
    project_root_str = str(cwd)
    python_path = env.get("PYTHONPATH", "")
    if project_root_str not in python_path.split(os.pathsep):
        env["PYTHONPATH"] = f"{project_root_str}{os.pathsep}{python_path}"
    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        cwd=cwd,
        bufsize=1,
        env=env
    )
    def stream_logger(stream, level):
        try:
            for line in iter(stream.readline, ''):
                if line:
                    system_log(level, line.strip())
        finally:
            stream.close()
    threading.Thread(
        target=stream_logger, args=(process.stdout, "INFO"), daemon=True
    ).start()
    threading.Thread(
        target=stream_logger, args=(process.stderr, "ERROR"), daemon=True
    ).start()
    return process

def create_public_portal(port, system_log):
    """將後端服務的埠號透過 Colab 的代理暴露出來。"""
    system_log("BATTLE", f"正在透過 Colab 代理暴露服務 (埠號: {port})...")
    try:
        colab_output.serve_kernel_port_as_iframe(port, width='100%', height='500')
        system_log("SUCCESS", "服務連結已生成。")
    except Exception as e:
        system_log("CRITICAL", f"透過 Colab 代理暴露服務失敗: {e}")

def terminate_process_tree(pid, system_log):
    """使用 psutil 遞歸地終止一個進程及其所有子進程。"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            system_log("INFO", f"正在終止子進程 (PID: {child.pid})...")
            child.terminate()
        gone, alive = psutil.wait_procs(children, timeout=3)
        for p in alive:
            system_log("WARNING", f"子進程 (PID: {p.pid}) 未能溫和終止，將強制結束。")
            p.kill()
        system_log("INFO", f"正在終止主進程 (PID: {parent.pid})...")
        parent.terminate()
        parent.wait(timeout=5)
        system_log("SUCCESS", f"進程樹 (PID: {pid}) 已成功終止。")
    except psutil.NoSuchProcess:
        system_log("INFO", f"嘗試終止進程 (PID: {pid}) 時，發現它已不存在。")
    except psutil.TimeoutExpired:
        system_log("WARNING", f"主進程 (PID: {pid}) 未能溫和終止，將強制結束。")
        parent.kill()
    except Exception as e:
        system_log("CRITICAL", f"終止進程樹時發生未預期的錯誤: {e}")

def archive_final_log(db_path, archive_dir, log_manager, filename_prefix="作戰日誌"):
    log_manager.log("INFO", "正在生成最終作戰報告...")
    if not db_path or not db_path.is_file():
        log_manager.log("WARNING", f"找不到日誌資料庫 ({db_path})，無法歸檔。")
        return
    try:
        archive_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.now(TAIPEI_TZ)
        archive_filename = f"{filename_prefix}_{now.strftime('%Y-%m-%d_%H-%M-%S')}.txt"
        archive_filepath = archive_dir / archive_filename
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True) as conn:
            logs = conn.execute(
                "SELECT timestamp, level, message FROM logs ORDER BY id ASC"
            ).fetchall()
        with open(archive_filepath, 'w', encoding='utf-8') as f:
            f.write("--- 鳳凰之心作戰日誌 v15.0 ---\n")
            f.write(f"報告生成時間: {now.isoformat()}\n")
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
    stats_dict = {}
    is_test_mode = os.environ.get("PHOENIX_TEST_MODE") == "1"

    try:
        archive_folder_name = config.get("archive_folder_name", "作戰日誌歸檔")
        fastapi_port = config.get("fastapi_port", 8000)
        sqlite_db_path = PROJECT_ROOT / "logs.sqlite"
        if sqlite_db_path.exists():
            sqlite_db_path.unlink()
        log_manager = LogManager(sqlite_db_path)

        if is_test_mode:
            def plain_logger(level, message):
                print(f"TEST_LOG: [{level}] {message}", flush=True)
                log_manager.log(level, message)
            system_log = plain_logger
        else:
            indicator = PrecisionIndicator(log_manager=log_manager, stats_dict=stats_dict)
            system_log = indicator.log
            indicator.start()

        system_log("INFO", f"專案根目錄 (動態偵測): {PROJECT_ROOT}")
        system_log("INFO", f"日誌資料庫將建立於: {sqlite_db_path}")
        system_log("BATTLE", "作戰流程啟動：正在安裝/驗證專案依賴...")
        uv_manager_path = PROJECT_ROOT / "uv_manager.py"
        if not uv_manager_path.is_file():
            system_log("WARNING", "未找到 'uv_manager.py'，將執行備用安裝流程。")
            system_log("INFO", "正在安裝 'uv' 工具...")
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "uv"],
                check=True, capture_output=True, text=True
            )
            system_log("INFO", "正在使用 'uv' 安裝 'requirements.txt'...")
            install_process = execute_and_stream(
                ["uv", "pip", "install", "-r", "requirements.txt"],
                PROJECT_ROOT, system_log
            )
        else:
            install_process = execute_and_stream(
                [sys.executable, "uv_manager.py"], PROJECT_ROOT, system_log
            )
        install_process.wait()
        if install_process.returncode != 0:
            raise RuntimeError("依賴安裝失敗，請檢查日誌輸出以了解詳細原因。作戰終止。")
        system_log("SUCCESS", "專案依賴已成功配置。")

        system_log("BATTLE", "正在啟動主應用伺服器...")
        SERVER_PROCESS = execute_and_stream(
            [sys.executable, "server_main.py", "--port", str(fastapi_port), "--host", "0.0.0.0"],
            PROJECT_ROOT, system_log
        )

        system_log("INFO", "準備啟動儀表板...")
        if indicator:
            indicator.activate()

        system_log("INFO", "等待 10 秒以確保伺服器完全啟動...")
        time.sleep(10)
        create_public_portal(fastapi_port, system_log)
        system_log("SUCCESS", "作戰系統已上線！要停止所有服務並歸檔日誌，請中斷此儲存格的執行。")

        while SERVER_PROCESS.poll() is None:
            if STOP_EVENT.is_set():
                break
            try:
                stats_dict['cpu'] = psutil.cpu_percent()
                stats_dict['ram'] = psutil.virtual_memory().percent
                stats_dict.setdefault('progress_label', '系統運行中')
            except psutil.Error:
                stats_dict['cpu'] = -1.0
                stats_dict['ram'] = -1.0
            time.sleep(1)

        if SERVER_PROCESS.poll() is not None and SERVER_PROCESS.returncode != 0:
            system_log("CRITICAL", f"後端進程意外終止，返回碼: {SERVER_PROCESS.returncode}")

    except KeyboardInterrupt:
        if 'system_log' in locals() and callable(system_log):
            system_log("WARNING", "\n[偵測到使用者手動中斷請求...正在準備安全關閉...]")
    except Exception as e:
        error_message = f"💥 作戰流程發生未預期的嚴重錯誤: {e}"
        print(f"\n{error_message}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        if 'system_log' in locals() and callable(system_log):
            system_log("CRITICAL", error_message)
            system_log("CRITICAL", traceback.format_exc())
            time.sleep(1)
    finally:
        STOP_EVENT.set()
        if 'system_log' in locals() and callable(system_log):
            system_log("BATTLE", "[正在執行終端清理程序...]")
        if SERVER_PROCESS and SERVER_PROCESS.poll() is None:
            terminate_process_tree(SERVER_PROCESS.pid, system_log)
        if indicator:
            indicator.stop()
        if log_manager and sqlite_db_path:
            archive_dir = PROJECT_ROOT / archive_folder_name
            filename_prefix = config.get("archive_filename_prefix", "作戰日誌")
            archive_final_log(sqlite_db_path, archive_dir, log_manager, filename_prefix=filename_prefix)
        elif 'system_log' in locals() and callable(system_log):
            system_log("ERROR", "無法歸檔日誌，因為最終資料庫路徑未能成功設定。")
        if 'system_log' in locals() and callable(system_log):
             system_log("SUCCESS", "部署流程已結束，所有服務已安全關閉。")
        print("\n--- 系統已安全關閉 ---")
