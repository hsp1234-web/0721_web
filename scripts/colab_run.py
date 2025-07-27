# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 colab_run.py (v9.0 穩定通訊最終版)                              ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       這是鳳凰之心指揮中心的最終版「一體化核心」。它整合了所有      ║
# ║       功能，並引入了穩健的 URL 獲取機制。                            ║
# ║                                                                      ║
# ║   v9.0 更新：                                                        ║
# ║       - 穩定 URL 獲取：根據您的正確建議，在獲取 Colab 公開 URL 時， ║
# ║         引入了「多次重試」機制。這將在伺服器啟動後，以 2 秒為間隔， ║
# ║         最多嘗試 5 次，極大提高了成功獲取並顯示網址的機率。          ║
# ║       - 最終穩定性：這是經過所有迭代後，最穩定、功能最完整的版本。   ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- Part 1: 匯入所有必要的函式庫 ---
import sys
import threading
import time
import collections
import shutil
import subprocess
import os
from pathlib import Path
from datetime import datetime

try:
    import psutil
    import pytz
    from IPython.display import clear_output
    from google.colab import output as colab_output
except ImportError as e:
    print(f"💥 核心套件匯入失敗: {e}")
    print("請確保在 Colab 環境中執行，並已安裝 psutil 與 pytz。")
    sys.exit(1)


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 2: 核心類別定義 (日誌、顯示管理器)                           █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

class LogManager:
    """一個執行緒安全的日誌管理器，負責集中管理所有日誌訊息。"""
    def __init__(self, timezone_str, max_logs=1000):
        self._logs = collections.deque(maxlen=max_logs)
        self._lock = threading.Lock()
        self.timezone = pytz.timezone(timezone_str)
        self.log_file_path = None

    def setup_file_logging(self, log_dir="logs"):
        log_dir_path = Path(log_dir)
        log_dir_path.mkdir(exist_ok=True)
        today_in_tz = datetime.now(self.timezone).strftime('%Y-%m-%d')
        self.log_file_path = log_dir_path / f"日誌-{today_in_tz}.md"

    def log(self, level: str, message: str):
        log_item = {"timestamp": datetime.now(self.timezone), "level": level.upper(), "message": message}
        with self._lock:
            self._logs.append(log_item)
            if self.log_file_path:
                try:
                    with open(self.log_file_path, 'a', encoding='utf-8') as f:
                        ts = log_item["timestamp"].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        f.write(f"[{ts}] [{log_item['level']}] {log_item['message']}\n")
                except Exception: pass

    def get_recent_logs(self, count: int) -> list:
        with self._lock:
            return list(self._logs)[-count:]

class DisplayManager:
    """視覺指揮官 (FRED 風格)：只使用 print() 進行高頻率重繪，根除閃爍。"""
    def __init__(self, stats: dict, log_manager: LogManager, log_lines_to_show: int, lock: threading.Lock, refresh_rate: float = 0.25):
        self._stats = stats
        self._log_manager = log_manager
        self._log_lines_to_show = log_lines_to_show
        self._refresh_rate = refresh_rate
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.STATUS_LIGHTS = {"正常": "🟢", "警告": "🟡", "錯誤": "🔴", "完成": "✅", "待機": "⚪️"}
        self._lock = lock

    def _run(self):
        """背景重繪迴圈。"""
        while not self._stop_event.is_set():
            try:
                clear_output(wait=True)
                self._draw_dashboard()
                time.sleep(self._refresh_rate)
            except Exception: pass

    def _draw_dashboard(self):
        """繪製單一影格的儀表板，只使用 print()。"""
        print("="*77)
        print("                      🚀 鳳凰之心指揮中心 v9.0 🚀                      ")
        print("="*77)
        print("\n---[ 最近日誌 ]-------------------------------------------------------------")
        recent_logs = self._log_manager.get_recent_logs(self._log_lines_to_show)
        for log in recent_logs:
            ts = log["timestamp"].strftime('%H:%M:%S.%f')[:-3]
            color = {"SUCCESS": "\033[92m", "WARNING": "\033[93m", "ERROR": "\033[91m", "BATTLE": "\033[96m", "SERVER": "\033[90m"}.get(log['level'], "\033[97m")
            reset_color = "\033[0m"
            print(f"[{ts}] {color}[{log['level']:<7}]{reset_color} {log['message']}")
        for _ in range(self._log_lines_to_show - len(recent_logs)): print()
        print("\n---[ 即時狀態 ]-------------------------------------------------------------")
        with self._lock:
            light = self.STATUS_LIGHTS.get(self._stats.get("light", "待機"), "⚪️")
            task_status = self._stats.get('task_status', '待命中...')
            app_url = self._stats.get("app_url", "網頁伺服器啟動中...")
        print(f"{light} 核心狀態：{task_status}")
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        ts = datetime.now(self._log_manager.timezone).strftime('%H:%M:%S')
        print(f"💻 硬體監控：[{ts}] CPU: {cpu:5.1f}% | RAM: {ram:5.1f}%")
        print("\n---[ 操作介面 ]-------------------------------------------------------------")
        print(f"🚀 開啟網頁介面 -> {app_url}")
        print("="*77)

    def start(self): self._thread.start()
    def stop(self):
        self._stop_event.set()
        if self._thread.is_alive(): self._thread.join(timeout=1)
        clear_output(wait=True)
        print("--- [DisplayManager] 視覺指揮官已停止運作 ---")


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 3: 主要業務邏輯與啟動協調器                                  █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

import concurrent.futures

def start_web_server(log_manager, stats, lock, port=8080):
    """在背景執行緒中啟動 FastAPI 伺服器並透過「主動超時重試機制」更新 URL。"""
    def kill_process_on_port(port):
        """使用 psutil 尋找並終止佔用指定埠的程序。"""
        log_manager.log("INFO", f"正在掃描並清理埠 {port}...")
        try:
            for proc in psutil.process_iter(['pid', 'name', 'connections']):
                for conn in proc.info.get('connections', []):
                    if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                        log_manager.log("WARNING", f"發現程序 {proc.info['name']} (PID: {proc.info['pid']}) 正在監聽埠 {port}。正在終止...")
                        p = psutil.Process(proc.info['pid'])
                        p.terminate()
                        p.wait(timeout=3)
                        log_manager.log("SUCCESS", f"程序 {proc.info['pid']} 已成功終止。")
                        return # 找到並殺掉一個就夠了
        except psutil.NoSuchProcess:
            log_manager.log("INFO", "沒有找到需要清理的舊程序。")
        except Exception as e:
            log_manager.log("ERROR", f"清理埠時發生錯誤: {e}")

    def get_colab_url(port):
        """嘗試獲取 Colab 公開 URL，此函式應在獨立執行緒中運行。"""
        try:
            return colab_output.eval_js(f'google.colab.kernel.proxyPort({port})')
        except Exception as e:
            log_manager.log("ERROR", f"獲取 URL 時內部發生錯誤: {e}")
            return None

    def server_thread():
        # **關鍵修正**: 使用 psutil 進行更可靠的清理
        kill_process_on_port(port)
        time.sleep(1)

        log_manager.log("BATTLE", f"正在背景啟動應用程式伺服器於埠號 {port}...")
        server_process = subprocess.Popen(
            [sys.executable, "main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )

        for line in iter(server_process.stdout.readline, ''):
            log_manager.log("SERVER", line.strip())
            if "Uvicorn running on" in line:
                log_manager.log("SUCCESS", "FastAPI 伺服器已成功啟動！正在獲取公開 URL...")

                # --- 主動超時重試機制 ---
                max_retries = 10
                total_timeout = 30
                single_try_timeout = 3
                url_found = False

                for attempt in range(max_retries):
                    log_manager.log("INFO", f"第 {attempt + 1}/{max_retries} 次嘗試獲取 URL (單次超時: {single_try_timeout}s)...")
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                        future = executor.submit(get_colab_url, port)
                        try:
                            app_url = future.result(timeout=single_try_timeout)
                            if app_url:
                                with lock:
                                    stats["app_url"] = app_url
                                log_manager.log("SUCCESS", f"網頁介面 URL 已成功獲取: {app_url}")
                                url_found = True
                                break
                        except concurrent.futures.TimeoutError:
                            log_manager.log("WARNING", f"第 {attempt + 1} 次嘗試獲取 URL 超時！")
                        except Exception as e:
                            log_manager.log("ERROR", f"第 {attempt + 1} 次嘗試中發生未預期錯誤: {e}")

                    if url_found:
                        break

                    time.sleep( (total_timeout / max_retries) - single_try_timeout )


                if not url_found:
                    error_msg = "在多次嘗試後，獲取 URL 依然失敗。"
                    with lock:
                        stats["app_url"] = error_msg
                    log_manager.log("ERROR", error_msg)

                break

        server_process.wait()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path, refresh_rate=0.2):
    """專案啟動主函數，由 Colab 儲存格呼叫"""
    display_manager = None
    stats = {"task_status": "準備中...", "light": "正常", "app_url": "等待伺服器啟動..."}
    lock = threading.Lock()
    STARTUP_TIMEOUT_SECONDS = 90 # 設定一個 90 秒的啟動超時

    try:
        log_manager = LogManager(timezone_str=timezone)
        display_manager = DisplayManager(stats, log_manager, log_lines_to_show=log_lines, lock=lock, refresh_rate=refresh_rate)
        display_manager.start()
        log_manager.log("INFO", "視覺指揮官已啟動。")

        log_manager.setup_file_logging(log_dir=project_path / "logs")
        log_manager.log("INFO", f"檔案日誌系統已設定，將記錄至 {log_manager.log_file_path}")
        
        # **關鍵修正**: 確保傳遞正確的埠號 8080
        start_web_server(log_manager, stats, lock, port=8080)
        
        with lock:
            stats["task_status"] = "伺服器啟動中，正在獲取網址..."

        # **關鍵修正**: 引入帶有進度條的優雅超時機制
        log_manager.log("INFO", f"伺服器啟動程序開始，最長等待 {STARTUP_TIMEOUT_SECONDS} 秒...")
        start_time = time.time()
        url_obtained = False
        while time.time() - start_time < STARTUP_TIMEOUT_SECONDS:
            with lock:
                current_url = stats.get("app_url", "")
                # 檢查 URL 是否已成功獲取
                if "https://" in current_url:
                    log_manager.log("SUCCESS", "伺服器 URL 已成功獲取，系統將保持運行。")
                    url_obtained = True
                    break
                # 檢查是否已明確失敗
                if "失敗" in current_url:
                    log_manager.log("ERROR", "伺服器啟動失敗，請檢查日誌。")
                    url_obtained = True # 也視為結束條件
                    break

            # 繪製進度條
            elapsed = time.time() - start_time
            progress = int((elapsed / STARTUP_TIMEOUT_SECONDS) * 40) # 40 個字元的進度條
            bar = "█" * progress + "-" * (40 - progress)
            print(f"\r[⏳] 正在等待伺服器啟動... [{bar}] {int(elapsed)}s / {STARTUP_TIMEOUT_SECONDS}s", end="")
            time.sleep(1)

        print() # 換行

        if not url_obtained:
            log_manager.log("ERROR", f"啟動超時！在 {STARTUP_TIMEOUT_SECONDS} 秒內未能獲取伺服器 URL。")
        else:
            # 如果成功，則進入無限迴圈以保持 Colab 活躍
            log_manager.log("INFO", "您可以隨時透過點擊 Colab 的「停止」按鈕來終止此程序。")
            while True:
                time.sleep(3600) # 減少 CPU 消耗

    except KeyboardInterrupt:
        if 'log_manager' in locals() and log_manager:
            log_manager.log("WARNING", "系統在運行中被手動中斷！")
    finally:
        if display_manager: display_manager.stop()
        if 'log_manager' in locals() and log_manager and archive_folder_name and archive_folder_name.strip():
            print("\n--- 執行日誌歸檔 (台北時區) ---")
            try:
                source_log_path = log_manager.log_file_path
                archive_folder_path = base_path / archive_folder_name.strip()
                if source_log_path and source_log_path.exists():
                    archive_folder_path.mkdir(exist_ok=True)
                    ts_str = datetime.now(log_manager.timezone).strftime("%Y%m%d_%H%M%S")
                    dest_path = archive_folder_path / f"日誌_{ts_str}.md"
                    shutil.copy2(source_log_path, dest_path)
                    print(f"✅ 日誌已成功歸檔至: {dest_path}")
                else:
                    print(f"⚠️  警告：找不到來源日誌檔 {source_log_path}。")
            except Exception as e: print(f"💥 歸檔期間發生錯誤: {e}")
        
        print("--- 鳳凰之心指揮中心程序已結束 ---")

# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 4: 可獨立執行區塊                                            █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

if __name__ == "__main__":
    """
    當這個腳本被直接執行時 (python scripts/colab_run.py)，
    這個區塊會被觸發。
    """
    print("--- [colab_run.py] 偵測到獨立執行模式，正在從環境變數讀取參數 ---")

    # 從環境變數讀取由啟動器傳入的參數，並提供合理的預設值
    log_lines = int(os.getenv("LOG_DISPLAY_LINES", 20))
    archive_folder_name = os.getenv("LOG_ARCHIVE_FOLDER_NAME", "作戰日誌歸檔")
    timezone = os.getenv("TIMEZONE", "Asia/Taipei")
    refresh_rate = float(os.getenv("REFRESH_RATE_SECONDS", 0.25))

    # Path 物件需要從字串轉換
    project_path_str = os.getenv("PROJECT_PATH")
    base_path_str = os.getenv("BASE_PATH")

    if not project_path_str or not base_path_str:
        print("💥 致命錯誤：環境變數 PROJECT_PATH 或 BASE_PATH 未設定。")
        sys.exit(1)

    project_path = Path(project_path_str)
    base_path = Path(base_path_str)

    print("✅ 參數讀取完成，準備啟動鳳凰之心核心...")

    # 呼叫主函數
    run_phoenix_heart(
        log_lines=log_lines,
        archive_folder_name=archive_folder_name,
        timezone=timezone,
        project_path=project_path,
        base_path=base_path,
        refresh_rate=refresh_rate
    )

# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 4: 可獨立執行區塊                                            █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

if __name__ == "__main__":
    """
    當這個腳本被直接執行時 (python scripts/colab_run.py)，
    這個區塊會被觸發。
    """
    print("--- [colab_run.py] 偵測到獨立執行模式，正在從環境變數讀取參數 ---")

    # 從環境變數讀取由啟動器傳入的參數，並提供合理的預設值
    log_lines = int(os.getenv("LOG_DISPLAY_LINES", 20))
    archive_folder_name = os.getenv("LOG_ARCHIVE_FOLDER_NAME", "作戰日誌歸檔")
    timezone = os.getenv("TIMEZONE", "Asia/Taipei")
    refresh_rate = float(os.getenv("REFRESH_RATE_SECONDS", 0.25))

    # Path 物件需要從字串轉換
    project_path_str = os.getenv("PROJECT_PATH")
    base_path_str = os.getenv("BASE_PATH")

    if not project_path_str or not base_path_str:
        print("💥 致命錯誤：環境變數 PROJECT_PATH 或 BASE_PATH 未設定。")
        sys.exit(1)

    project_path = Path(project_path_str)
    base_path = Path(base_path_str)

    print("✅ 參數讀取完成，準備啟動鳳凰之心核心...")

    # 呼叫主函數
    run_phoenix_heart(
        log_lines=log_lines,
        archive_folder_name=archive_folder_name,
        timezone=timezone,
        project_path=project_path,
        base_path=base_path,
        refresh_rate=refresh_rate
    )
