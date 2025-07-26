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
        # 從 stats_dict 獲取數據，提供預設值以防萬一
        cpu_perc = self.stats_dict.get('cpu', 0.0)
        ram_perc = self.stats_dict.get('ram', 0.0)

        # 獲取服務狀態，如果不存在則顯示 '⏳'
        fastapi_status = self.stats_dict.get('fastapi_status', '⏳')
        websocket_status = self.stats_dict.get('websocket_status', '⏳')
        db_status = self.stats_dict.get('db_status', '⏳')
        db_latency = self.stats_dict.get('db_latency', 'N/A')

        # 格式化面板內容
        cpu_bar = self._create_progress_bar(cpu_perc)
        ram_bar = self._create_progress_bar(ram_perc)

        line1 = f"│┌─ ⚙️ 即時資源監控 ───────────┐ ┌─ 🌐 核心服務狀態 ───────────┐│"
        line2 = f"││ CPU: {cpu_bar}   │ │ {fastapi_status} 後端 FastAPI 引擎        ││"
        line3 = f"││ RAM: {ram_bar}   │ │ {websocket_status} WebSocket 通訊頻道       ││"
        line4 = f"││                           │ │ {db_status} 日誌資料庫 (延遲: {db_latency: <5}) ││"
        line5 = f"│└───────────────────────────┘ └───────────────────────────┘│"

        header = "┌─────────────────────────── 鳳凰之心 v14.0 駕駛艙 ───────────────────────────┐"

        return "\n".join([header, line1, line2, line3, line4, line5])

    def _render_log_panel(self):
        """渲染儀表板的日誌面板。"""
        header = "├─────────────────────────── 近況彙報 (最新 5 條) ───────────────────────────┤"

        # 定義日誌等級的顏色和圖示
        log_styles = {
            "SUCCESS": ("\x1b[32m", "✅"), "ERROR": ("\x1b[31m", "🔴"),
            "CRITICAL": ("\x1b[91m", "🔥"), "WARNING": ("\x1b[33m", "🟡"),
            "BATTLE": ("\x1b[34m", "⚡"), "INFO": ("\x1b[37m", "✨"),
            "DEFAULT": ("\x1b[0m", "🔹")
        }

        lines = []
        num_logs = 5

        # 從 deque 的右側（最新）開始取日誌
        recent_logs = list(self.log_deque)[-num_logs:]

        for i in range(num_logs):
            if i < len(recent_logs):
                timestamp, level, message = recent_logs[i]

                color, icon = log_styles.get(level.upper(), log_styles["DEFAULT"])
                reset_color = log_styles["DEFAULT"][0]

                ts_str = timestamp.strftime('%H:%M:%S')
                level_str = f"[{level.upper():^7}]"

                # 截斷過長的訊息以避免破壞版面
                max_msg_len = 58
                message_str = message[:max_msg_len] + '...' if len(message) > max_msg_len else message

                line = f"│[{ts_str}] {color}{level_str}{reset_color} {icon} {message_str:<61}│"
                lines.append(line)
            else:
                # 如果日誌不足，用空行填充
                lines.append("│" + " " * 78 + "│")

        footer = "└──────────────────────────────────────────────────────────────────────────┘"

        return "\n".join([header] + lines + [footer])


    def _render_status_bar(self):
        """渲染儀表板底部的狀態欄。"""
        # 定義 ANSI 顏色碼
        BG_COLOR = "\x1b[44m"  # 藍色背景
        RESET = "\x1b[0m"

        # 獲取數據
        cpu_perc = self.stats_dict.get('cpu', 0.0)
        ram_perc = self.stats_dict.get('ram', 0.0)
        system_status = self.stats_dict.get('system_status', '系統狀態未知')
        time_str = datetime.now(TAIPEI_TZ).strftime('%H:%M:%S')

        # 組合字串
        status_line = f" CPU: {cpu_perc:5.1f}% | RAM: {ram_perc:5.1f}% | {system_status} | {time_str} "

        # 讓狀態欄填滿整個寬度 (80 個字元)
        padded_line = status_line.ljust(80)

        return f"{BG_COLOR}{padded_line}{RESET}"

    def _run(self):
        """
        背景渲染執行緒的主迴圈。
        負責以固定頻率重繪整個儀表板。
        """
        # 執行緒啟動後，在此處等待，直到 activate() 方法被呼叫
        self.activated.wait()

        while not self.stop_event.is_set():
            try:
                # 清除畫面
                clear_output(wait=True)

                # 依序渲染各個面板
                top_panel = self._render_top_panel()
                log_panel = self._render_log_panel()
                status_bar = self._render_status_bar()

                # 組合成最終畫面並打印
                full_screen = f"{top_panel}\n{log_panel}\n{status_bar}"
                print(full_screen, end="", flush=True)

            except Exception as e:
                # 在主迴圈中捕獲異常，防止渲染執行緒崩潰
                print(f"儀表板渲染錯誤: {e}")

            time.sleep(0.2)

# ==============================================================================
# SECTION 3: 核心輔助函式
# ==============================================================================
def execute_and_stream(cmd, cwd, system_log):
    # 創建一個環境變量的副本，以傳遞給子進程
    env = os.environ.copy()

    # 確保 PYTHONPATH 包含專案根目錄，以便子進程能找到模組
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
        env=env  # 傳遞完整的環境變量副本
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

def create_public_portal(port, system_log):
    """將後端服務的埠號透過 Colab 的代理暴露出來。"""
    system_log("BATTLE", f"正在透過 Colab 代理暴露服務 (埠號: {port})...")
    try:
        # 這裡不再需要重定向到特定元素，直接在儲存格底部輸出連結
        colab_output.serve_kernel_port_as_iframe(port, width='100%', height='500')
        system_log("SUCCESS", "服務連結已生成。")
    except Exception as e:
        system_log("CRITICAL", f"透過 Colab 代理暴露服務失敗: {e}")

def terminate_process_tree(pid, system_log):
    """使用 psutil 遞歸地終止一個進程及其所有子進程。"""
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)

        # 先終止子進程
        for child in children:
            system_log("INFO", f"正在終止子進程 (PID: {child.pid})...")
            child.terminate()

        # 等待子進程終止
        gone, alive = psutil.wait_procs(children, timeout=3)
        for p in alive:
            system_log("WARNING", f"子進程 (PID: {p.pid}) 未能溫和終止，將強制結束。")
            p.kill()

        # 最後終止父進程
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

    # 測試模式下，簡化日誌記錄，禁用UI
    is_test_mode = os.environ.get("PHOENIX_TEST_MODE") == "1"

    try:
        # 步驟 1: 解構設定並啟動日誌與指示器
        archive_folder_name = config.get("archive_folder_name", "作戰日誌歸檔")
        fastapi_port = config.get("fastapi_port", 8000)

        sqlite_db_path = PROJECT_ROOT / "logs.sqlite"
        if sqlite_db_path.exists():
            sqlite_db_path.unlink()

        log_manager = LogManager(sqlite_db_path)

        if is_test_mode:
            # 在測試模式下，使用簡單的 print 進行日誌記錄
            def plain_logger(level, message):
                print(f"TEST_LOG: [{level}] {message}", flush=True)
                log_manager.log(level, message) # 仍然寫入資料庫以供歸檔驗證
            system_log = plain_logger
        else:
            # 正常模式下，使用帶有 UI 的 PrecisionIndicator
            indicator = PrecisionIndicator(log_manager=log_manager, stats_dict=stats_dict)
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
            [sys.executable, "server_main.py", "--port", str(fastapi_port), "--host", "0.0.0.0"],
            PROJECT_ROOT, system_log
        )

        # 步驟 5: 活化儀表板並嵌入介面
        system_log("INFO", "準備啟動儀表板...")
        indicator.activate() # <<-- 關鍵步驟：現在才啟動儀表板渲染

        system_log("INFO", "等待 10 秒以確保伺服器完全啟動...")
        time.sleep(10)

        create_public_portal(fastapi_port, system_log)

        system_log("SUCCESS", "作戰系統已上線！要停止所有服務並歸檔日誌，請中斷此儲存格的執行。")

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
            terminate_process_tree(SERVER_PROCESS.pid, system_log)

        if indicator:
            indicator.stop()

        if log_manager and sqlite_db_path:
            archive_dir = PROJECT_ROOT / archive_folder_name
            # 從設定中讀取檔案名前綴，如果沒有則使用預設值
            filename_prefix = config.get("archive_filename_prefix", "作戰日誌")
            archive_final_log(sqlite_db_path, archive_dir, log_manager, filename_prefix=filename_prefix)
        elif 'system_log' in locals():
            # 如果 log_manager 因故不存在，但 system_log 存在，至少要發出一個警告
            system_log("ERROR", "無法歸檔日誌，因為最終資料庫路徑未能成功設定。")

        if 'system_log' in locals():
             system_log("SUCCESS", "部署流程已結束，所有服務已安全關閉。")

        print("\n--- 系統已安全關閉 ---")
