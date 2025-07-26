# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 colab_run.py (v8.0 功能完整最終版)                              ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       這是鳳凰之心指揮中心的最終版「一體化核心」。它整合了所有      ║
# ║       功能，包括：                                                   ║
# ║       1. FRED 風格的無閃爍儀表板 (`clear_output(wait=True)`)。       ║
# ║       2. 可平滑滾動的日誌顯示區。                                    ║
# ║       3. 在背景啟動 FastAPI 伺服器。                                 ║
# ║       4. 自動生成並在儀表板上顯示可點擊的網頁介面 URL。              ║
# ║                                                                      ║
# ║   v8.0 更新：                                                        ║
# ║       - 功能整合：加入了在背景啟動 web 伺服器的完整邏輯。          ║
# ║       - URL 生成：能夠自動獲取並顯示 Colab 的公開 URL。              ║
# ║       - 滾動展示：延長了作戰演習的日誌數量，以清晰展示滾動效果。     ║
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
    def __init__(self, stats: dict, log_manager: LogManager, log_lines_to_show: int, refresh_rate: float = 0.25):
        self._stats = stats
        self._log_manager = log_manager
        self._log_lines_to_show = log_lines_to_show
        self._refresh_rate = refresh_rate
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.STATUS_LIGHTS = {"正常": "🟢", "警告": "🟡", "錯誤": "🔴", "完成": "✅", "待機": "⚪️"}

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
        print("╔═════════════════════════════════════════════════════════════════════════╗")
        print("║                      🚀 鳳凰之心指揮中心 v8.0 🚀                      ║")
        print("╚═════════════════════════════════════════════════════════════════════════╝")
        print("\n---[ 最近日誌 ]-------------------------------------------------------------")
        recent_logs = self._log_manager.get_recent_logs(self._log_lines_to_show)
        for log in recent_logs:
            ts = log["timestamp"].strftime('%H:%M:%S.%f')[:-3]
            color = {"SUCCESS": "\033[92m", "WARNING": "\033[93m", "ERROR": "\033[91m", "BATTLE": "\033[96m"}.get(log['level'], "\033[97m")
            reset_color = "\033[0m"
            print(f"[{ts}] {color}[{log['level']:<7}]{reset_color} {log['message']}")
        for _ in range(self._log_lines_to_show - len(recent_logs)): print()
        print("\n---[ 即時狀態 ]-------------------------------------------------------------")
        light = self.STATUS_LIGHTS.get(self._stats.get("light", "待機"), "⚪️")
        print(f"{light} 核心狀態：{self._stats.get('task_status', '待命中...')}")
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        ts = datetime.now(self._log_manager.timezone).strftime('%H:%M:%S')
        print(f"💻 硬體監控：[{ts}] CPU: {cpu:5.1f}% | RAM: {ram:5.1f}%")
        print("\n---[ 操作介面 ]-------------------------------------------------------------")
        link = self._stats.get("app_url", "網頁伺服器啟動中...")
        print(f"🚀 開啟網頁介面 -> {link}")
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

def start_web_server(log_manager, stats, port=8000):
    """在背景執行緒中啟動 FastAPI 伺服器並更新 URL。"""
    def server_thread():
        log_manager.log("INFO", "正在嘗試清理舊的伺服器程序...")
        subprocess.run(f"fuser -k -n tcp {port}", shell=True, capture_output=True)
        time.sleep(1)
        
        log_manager.log("BATTLE", f"正在背景啟動 FastAPI 伺服器於埠號 {port}...")
        
        # 使用 Popen 在背景啟動伺服器
        server_process = subprocess.Popen(
            [sys.executable, "server_main.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # 將錯誤合併到標準輸出
            text=True,
            encoding='utf-8'
        )
        
        # 監控伺服器輸出，直到它成功啟動
        for line in iter(server_process.stdout.readline, ''):
            # 將伺服器的日誌也記錄下來，方便除錯
            log_manager.log("SERVER", line.strip())
            if "Uvicorn running on" in line:
                log_manager.log("SUCCESS", "FastAPI 伺服器已成功啟動！")
                try:
                    # 獲取 Colab 公開 URL
                    app_url = colab_output.eval_js(f'google.colab.kernel.proxyPort({port})')
                    stats["app_url"] = app_url
                    log_manager.log("SUCCESS", f"網頁介面 URL 已生成: {app_url}")
                except Exception as e:
                    stats["app_url"] = f"URL 生成失敗: {e}"
                    log_manager.log("ERROR", stats["app_url"])
                break # 成功後跳出監控迴圈
        
        # 讓伺服器在背景持續運行
        server_process.wait()

    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()

def main_execution_logic(log_manager, stats, log_lines_to_show):
    """專案的主要業務邏輯 (延長版)"""
    try:
        stats["light"] = "正常"
        stats["task_status"] = "正在執行主要任務"
        log_manager.log("INFO", "主業務邏輯開始執行...")
        
        # 產生足夠多的日誌以觸發滾動效果
        total_tasks = log_lines_to_show + 15 
        for i in range(1, total_tasks + 1):
            log_manager.log("BATTLE", f"正在處理第 {i}/{total_tasks} 階段的戰鬥任務...")
            stats["task_status"] = f"任務進度 {i}/{total_tasks}"
            time.sleep(0.3)
            if i == 15:
                stats["light"] = "警告"
                log_manager.log("WARNING", "偵測到 API 回應延遲，已自動重試...")
            if i % 10 == 0:
                stats["light"] = "正常"
                log_manager.log("SUCCESS", f"第 {i} 階段作戰節點順利完成！")
        
        stats["light"] = "完成"
        stats["task_status"] = "所有主要業務邏輯已成功執行完畢！"
        log_manager.log("SUCCESS", stats["task_status"])
        
        time.sleep(2)
        stats["light"] = "待機"
        stats["task_status"] = "任務完成，系統待命中"

    except KeyboardInterrupt:
        stats["light"] = "警告"; stats["task_status"] = "使用者手動中斷"
        log_manager.log("WARNING", "偵測到手動中斷信號！")
    except Exception as e:
        stats["light"] = "錯誤"; stats["task_status"] = f"發生致命錯誤！"
        log_manager.log("ERROR", f"主業務邏輯發生未預期錯誤: {e}")

def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path):
    """專案啟動主函數，由 Colab 儲存格呼叫"""
    display_manager = None
    stats = {"task_status": "準備中...", "light": "正常", "app_url": "等待伺服器啟動..."}

    try:
        log_manager = LogManager(timezone_str=timezone)
        display_manager = DisplayManager(stats, log_manager, log_lines_to_show=log_lines)
        display_manager.start()
        log_manager.log("INFO", "視覺指揮官已啟動。")

        log_manager.setup_file_logging(log_dir=project_path / "logs")
        log_manager.log("INFO", f"檔案日誌系統已設定，將記錄至 {log_manager.log_file_path}")
        
        # --- 啟動網頁伺服器 ---
        start_web_server(log_manager, stats, port=8000)
        
        log_manager.log("SUCCESS", "所有服務已成功啟動，指揮中心上線！")
        main_execution_logic(log_manager, stats, log_lines)

        while True: time.sleep(1)

    except KeyboardInterrupt:
        if 'log_manager' in locals() and log_manager:
            log_manager.log("WARNING", "系統在運行中被手動中斷！")
    finally:
        if display_manager: display_manager.stop()
        if 'log_manager' in locals() and log_manager and archive_folder_name and archive_folder_name.strip():
            print(f"\n--- 執行日誌歸檔 (台北時區) ---")
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

