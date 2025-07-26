# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 colab_run.py (v6.0 FRED 風格最終版)                             ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       這是鳳凰之心指揮中心的最終版「一體化核心」。它全面採納了您      ║
# ║       所欣賞的「FRED 工具」設計哲學，使用「高頻率全螢幕重繪」技術，   ║
# ║       提供一個絕對整潔、穩定、且版面佈局正確的儀表板。               ║
# ║                                                                      ║
# ║   v6.0 更新：                                                        ║
# ║       - 終極架構回歸：全面採用 `clear_output(wait=True)` 為核心，     ║
# ║         根除所有排版混亂與閃爍問題。                                 ║
# ║       - 版面修正：嚴格依照您的要求，將標題置頂，按鈕置底。         ║
# ║       - 狀態燈號：引入 🟢 🟡 🔴 燈號，讓核心狀態一目了然。         ║
# ║       - 程式碼整合：所有必要邏輯皆在此單一檔案中，簡化維護。       ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- Part 1: 匯入所有必要的函式庫 ---
import sys
import threading
import time
import collections
import shutil
from pathlib import Path
from datetime import datetime

try:
    import psutil
    import pytz
    from IPython.display import display, clear_output, HTML
except ImportError as e:
    print(f"💥 核心套件匯入失敗: {e}")
    print("請確保在 Colab 儲存格中已透過 requirements.txt 正確安裝 psutil 與 pytz。")
    sys.exit(1)


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 2: 核心類別定義 (日誌、顯示管理器)                           █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

class LogManager:
    """
    一個執行緒安全的日誌管理器，負責集中管理所有日誌訊息。
    """
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
        log_item = {
            "timestamp": datetime.now(self.timezone),
            "level": level.upper(),
            "message": message
        }
        with self._lock:
            self._logs.append(log_item)
            if self.log_file_path:
                try:
                    with open(self.log_file_path, 'a', encoding='utf-8') as f:
                        ts = log_item["timestamp"].strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                        f.write(f"[{ts}] [{log_item['level']}] {log_item['message']}\n")
                except Exception:
                    # 在主循環中忽略檔案寫入錯誤，避免中斷
                    pass

    def get_recent_logs(self, count: int) -> list:
        with self._lock:
            return list(self._logs)[-count:]

class DisplayManager:
    """
    視覺指揮官 (FRED 風格)：負責高頻率重繪整個儀表板畫面。
    """
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
                # 這是實現「不洗版」更新的核心
                clear_output(wait=True)
                self._draw_dashboard()
                time.sleep(self._refresh_rate)
            except Exception:
                # 在顯示迴圈中捕獲異常，避免主程式崩潰
                pass

    def _draw_dashboard(self):
        """繪製單一影格的儀表板。"""
        # --- Part A: 標題 ---
        print("╔═════════════════════════════════════════════════════════════════════════╗")
        print("║                      🚀 鳳凰之心指揮中心 v6.0 🚀                      ║")
        print("╚═════════════════════════════════════════════════════════════════════════╝")

        # --- Part B: 日誌區 ---
        print("\n---[ 最近日誌 ]-------------------------------------------------------------")
        recent_logs = self._log_manager.get_recent_logs(self._log_lines_to_show)
        for log in recent_logs:
            ts = log["timestamp"].strftime('%H:%M:%S.%f')[:-3]
            # 使用 ANSI 顏色代碼
            color = {"SUCCESS": "\033[92m", "WARNING": "\033[93m", "ERROR": "\033[91m", "BATTLE": "\033[96m"}.get(log['level'], "\033[97m")
            reset_color = "\033[0m"
            print(f"[{ts}] {color}[{log['level']:<7}]{reset_color} {log['message']}")
        # 打印空行以保持日誌區高度穩定
        for _ in range(self._log_lines_to_show - len(recent_logs)):
            print()

        # --- Part C: 狀態區 ---
        print("\n---[ 即時狀態 ]-------------------------------------------------------------")
        light = self.STATUS_LIGHTS.get(self._stats.get("light", "待機"), "⚪️")
        print(f"{light} 核心狀態：{self._stats.get('task_status', '待命中...')}")
        
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        ts = datetime.now(self._log_manager.timezone).strftime('%H:%M:%S')
        print(f"💻 硬體監控：[{ts}] CPU: {cpu:5.1f}% | RAM: {ram:5.1f}%")

        # --- Part D: 按鈕區 (透過 display 顯示 HTML) ---
        button_html = """
        <div style="border-top: 2px solid #00BCD4; padding-top: 10px; margin-top: 15px;">
            <p style="text-align:center; margin:0;">
                <a href="YOUR_FASTAPI_URL_PLACEHOLDER" target="_blank" style="background-color:#00BCD4; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">
                    開啟網頁操作介面
                </a>
            </p>
        </div>
        """
        display(HTML(button_html))

    def start(self):
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread.is_alive():
            self._thread.join(timeout=1)
        # 停止後，最後一次清理畫面並顯示最終訊息
        clear_output(wait=True)
        print("--- [DisplayManager] 視覺指揮官已停止運作 ---")


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 3: 主要業務邏輯與啟動協調器                                  █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

def main_execution_logic(log_manager, stats):
    """專案的主要業務邏輯"""
    try:
        stats["light"] = "正常"
        stats["task_status"] = "正在執行主要任務"
        log_manager.log("INFO", "主業務邏輯開始執行...")
        
        for i in range(1, 11):
            log_manager.log("BATTLE", f"正在處理第 {i}/10 階段的戰鬥任務...")
            stats["task_status"] = f"任務進度 {i}/10"
            time.sleep(0.5)
            if i == 7:
                stats["light"] = "警告"
                log_manager.log("WARNING", "偵測到 API 回應延遲，已自動重試...")
            if i % 5 == 0:
                stats["light"] = "正常" # 恢復正常燈號
                log_manager.log("SUCCESS", f"第 {i} 階段作戰節點順利完成！")
        
        stats["light"] = "完成"
        stats["task_status"] = "所有主要業務邏輯已成功執行完畢！"
        log_manager.log("SUCCESS", stats["task_status"])
        
        time.sleep(2)
        stats["light"] = "待機"
        stats["task_status"] = "任務完成，系統待命中"

    except KeyboardInterrupt:
        stats["light"] = "警告"
        stats["task_status"] = "使用者手動中斷"
        log_manager.log("WARNING", "偵測到手動中斷信號！")
    except Exception as e:
        stats["light"] = "錯誤"
        stats["task_status"] = f"發生致命錯誤！"
        log_manager.log("ERROR", f"主業務邏輯發生未預期錯誤: {e}")

def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path):
    """專案啟動主函數，由 Colab 儲存格呼叫"""
    display_manager = None
    
    # 共享的狀態字典
    stats = {
        "task_status": "準備中...",
        "light": "正常" # 狀態燈號: 正常, 警告, 錯誤, 完成, 待機
    }

    try:
        # --- 1. 初始化日誌與顯示管理器 ---
        log_manager = LogManager(timezone_str=timezone)
        display_manager = DisplayManager(stats, log_manager, log_lines_to_show=log_lines)

        # --- 2. 啟動顯示迴圈 ---
        display_manager.start()
        log_manager.log("INFO", "視覺指揮官已啟動。")

        # --- 3. 設定檔案日誌 ---
        log_manager.setup_file_logging(log_dir=project_path / "logs")
        log_manager.log("INFO", f"檔案日誌系統已設定，將記錄至 {log_manager.log_file_path}")
        
        log_manager.log("SUCCESS", "所有服務已成功啟動，指揮中心上線！")

        # --- 4. 執行主要業務邏輯 ---
        main_execution_logic(log_manager, stats)

        # --- 5. 保持待命 ---
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        if 'log_manager' in locals() and log_manager:
            log_manager.log("WARNING", "系統在運行中被手動中斷！")
    finally:
        # --- 6. 優雅關閉 ---
        if display_manager:
            display_manager.stop()

        # --- 7. 執行日誌歸檔 ---
        if 'log_manager' in locals() and log_manager and archive_folder_name and archive_folder_name.strip():
            # 在主控台打印，因為顯示管理器已停止
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
            except Exception as e:
                print(f"💥 歸檔期間發生錯誤: {e}")
        
        print("--- 鳳凰之心指揮中心程序已結束 ---")
