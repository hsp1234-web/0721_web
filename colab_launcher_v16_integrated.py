# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 儲存格 v16 (返璞歸真版)                                   ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       返璞歸真。在 Colab 的特殊環境下，試圖分離啟動器與核心邏輯，   ║
# ║       會引入無法預測的 `import` 和 `subprocess` 問題。本版本採用     ║
# ║       「單體整合」策略，將所有邏輯放在一個檔案中，確保 100% 的穩定性。║
# ║                                                                      ║
# ║   v16 更新 (Jules 修正):                                             ║
# ║       - 單體整合：將所有核心邏輯 (日誌、顯示、伺服器啟動) 全部整合。 ║
# ║       - 優雅超時：引入帶進度條的 90 秒啟動超時，不再無限等待。       ║
# ║       - 根除埠衝突：採用 `psutil` 進行精準的埠清理，解決當機問題。     ║
# ║       - 安裝進度條：移除 `-q` 參數，讓使用者可以看到安裝過程。         ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心指揮中心 v16 (返璞歸真版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "2.1.2" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 應用程式參數**
#@markdown > **設定指揮中心的核心運行參數。**
#@markdown ---
#@markdown **儀表板更新頻率 (秒) (REFRESH_RATE_SECONDS)**
REFRESH_RATE_SECONDS = 0.25 #@param {type:"number"}
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
LOG_DISPLAY_LINES = 20 #@param {type:"integer"}
#@markdown **日誌歸檔資料夾 (LOG_ARCHIVE_FOLDER_NAME)**
#@markdown > **留空即關閉歸檔功能。**
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **時區設定 (TIMEZONE)**
TIMEZONE = "Asia/Taipei" #@param {type:"string"}

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心啟動器 v16
# ==============================================================================
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
import threading
import collections
from datetime import datetime

def ultimate_bootstrap_v16():
    """
    單體整合式啟動器，將所有準備工作和核心邏輯放在同一個程序中執行。
    """
    # **關鍵修正**: 根據環境變數決定 base_path，以適應模擬測試環境
    is_simulation = os.getenv("SIMULATION_MODE") == "true"
    base_path = Path.cwd() / "mock_content" if is_simulation else Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    # --- 步驟 1: 環境準備 ---
    try:
        from IPython.display import clear_output
        clear_output(wait=True)

        print("🚀 鳳凰之心 v16 [返璞歸真版] 啟動程序...")
        print("="*80)

        print("\n--- 步驟 1/3: 準備下載目錄 ---")
        if FORCE_REPO_REFRESH and project_path.exists():
            print(f"⚠️  偵測到「強制刷新」，正在刪除舊資料夾: {project_path}")
            shutil.rmtree(project_path)
            print("✅  舊資料夾已移除。")

        base_path.mkdir(exist_ok=True)
        if not project_path.exists():
            print(f"🚀 開始從 GitHub (分支/標籤: {TARGET_BRANCH_OR_TAG}) 拉取程式碼...")
            git_command = ["git", "clone", "-q", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", REPOSITORY_URL, str(project_path)]
            subprocess.run(git_command, check=True, cwd=base_path)
            print("✅ 程式碼成功下載！")

        os.chdir(project_path)
        print(f"✅ 工作目錄已切換至: {os.getcwd()}")

        # --- 步驟 2: 安裝依賴 ---
        print("\n--- 步驟 2/3: 安裝依賴 (將顯示進度條) ---")
        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            # 安裝核心及專案依賴
            subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "pytz", "IPython", "-r", str(requirements_path)], check=True)
            print("✅ 所有依賴套件已成功安裝。")
        else:
            print("⚠️  警告：找不到 'requirements.txt'，跳過依賴安裝。")

    except Exception as e:
        print(f"\n💥 環境準備階段發生嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
        return # 準備失敗，直接退出

    # --- 步驟 3: 執行核心邏輯 ---
    print("\n--- 步驟 3/3: 啟動指揮中心核心 ---")

    # ==========================================================================
    #  核心邏輯：直接整合，確保在同一環境中運行
    # ==========================================================================
    try:
        import psutil
        import pytz
        from google.colab import output as colab_output

        # --- 核心類別 ---
        class LogManager:
            def __init__(self, timezone_str, max_logs=1000):
                self._logs, self._lock, self.timezone, self.log_file_path = collections.deque(maxlen=max_logs), threading.Lock(), pytz.timezone(timezone_str), None
            def setup_file_logging(self, log_dir="logs"):
                Path(log_dir).mkdir(exist_ok=True)
                self.log_file_path = Path(log_dir) / f"日誌-{datetime.now(self.timezone).strftime('%Y-%m-%d')}.md"
            def log(self, level: str, message: str):
                log_item = {"timestamp": datetime.now(self.timezone), "level": level.upper(), "message": message}
                with self._lock: self._logs.append(log_item)
            def get_recent_logs(self, count: int) -> list:
                with self._lock: return list(self._logs)[-count:]

        class DisplayManager:
            def __init__(self, stats, log_manager, log_lines, lock, refresh_rate):
                self._stats, self._log_manager, self._log_lines, self._lock, self._refresh_rate = stats, log_manager, log_lines, lock, refresh_rate
                self._stop_event, self._thread = threading.Event(), threading.Thread(target=self._run, daemon=True)
            def _run(self):
                while not self._stop_event.is_set():
                    try:
                        clear_output(wait=True)
                        print("="*80 + "\n                      🚀 鳳凰之心指揮中心 v16 🚀\n" + "="*80)
                        recent_logs = self._log_manager.get_recent_logs(self._log_lines)
                        for log in recent_logs: print(f"[{log['timestamp'].strftime('%H:%M:%S')}] [{log['level']}] {log['message']}")
                        with self._lock: app_url = self._stats.get("app_url", "啟動中...")
                        print(f"\n🚀 開啟網頁介面 -> {app_url}\n" + "="*80)
                        time.sleep(self._refresh_rate)
                    except Exception: pass
            def start(self): self._thread.start()
            def stop(self): self._stop_event.set()

        # --- 核心函式 ---
        def kill_process_on_port(port, log_manager):
            try:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    for conn in proc.info.get('connections', []):
                        if conn.laddr.port == port and conn.status == psutil.CONN_LISTEN:
                            log_manager.log("WARNING", f"發現程序 PID:{proc.info['pid']} 正在監聽埠 {port}，將其終止。")
                            psutil.Process(proc.info['pid']).terminate()
            except Exception as e: log_manager.log("ERROR", f"清理埠 {port} 時發生錯誤: {e}")

        def start_web_server(port, log_manager, stats, lock):
            kill_process_on_port(port, log_manager)
            def server_thread():
                log_manager.log("BATTLE", f"正在背景啟動應用程式伺服器於埠號 {port}...")
                server_process = subprocess.Popen([sys.executable, "main.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
                for line in iter(server_process.stdout.readline, ''):
                    log_manager.log("SERVER", line.strip())
                    if "Uvicorn running on" in line or "Serving Flask app" in line:
                        log_manager.log("SUCCESS", "偵測到伺服器啟動信號！正在獲取公開 URL...")
                        try:
                            app_url = colab_output.eval_js(f'google.colab.kernel.proxyPort({port})')
                            with lock: stats["app_url"] = app_url
                        except Exception:
                            with lock: stats["app_url"] = "獲取 URL 失敗"
                        break
            threading.Thread(target=server_thread, daemon=True).start()

        # --- 執行主體 ---
        stats, lock = {"app_url": "等待伺服器啟動..."}, threading.Lock()
        log_manager = LogManager(timezone_str=TIMEZONE)
        display_manager = DisplayManager(stats, log_manager, LOG_DISPLAY_LINES, lock, REFRESH_RATE_SECONDS)
        display_manager.start()
        log_manager.log("INFO", "指揮中心核心已啟動。")
        log_manager.setup_file_logging()

        start_web_server(8080, log_manager, stats, lock)

        # 優雅的超時等待
        STARTUP_TIMEOUT_SECONDS = 90
        start_time = time.time()
        url_obtained = False
        while time.time() - start_time < STARTUP_TIMEOUT_SECONDS:
            with lock:
                if "https://" in stats.get("app_url", ""):
                    log_manager.log("SUCCESS", f"伺服器 URL 已成功獲取: {stats['app_url']}")
                    url_obtained = True
                    break
            elapsed = time.time() - start_time
            bar = "█" * int((elapsed / STARTUP_TIMEOUT_SECONDS) * 40)
            print(f"\r[⏳] 正在等待伺服器 URL... [{bar:<40}] {int(elapsed)}s", end="")
            time.sleep(1)

        print()
        if url_obtained:
            log_manager.log("INFO", "系統將保持運行。您可以隨時透過點擊 Colab 的「停止」按鈕來終止此程序。")
            while True: time.sleep(3600)
        else:
            log_manager.log("ERROR", f"啟動超時！在 {STARTUP_TIMEOUT_SECONDS} 秒內未能獲取伺服器 URL。")

    except KeyboardInterrupt:
        print("\n\n[INFO] 偵測到手動中斷，程序即將結束。")
    except Exception as e:
        print(f"\n💥 指揮中心核心發生未預期的嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\n--- 鳳凰之心指揮中心程序已結束 ---")

# --- 執行啟動程序 ---
ultimate_bootstrap_v16()
