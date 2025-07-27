#@title 💎 鳳凰之心指揮中心 v12 (終極整合版) { vertical-output: true, display-mode: "form" }
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
# 🚀 核心啟動器 v12 (Jules 終極整合版)
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
import concurrent.futures

def ultimate_bootstrap():
    """
    終極的、單一檔案的啟動器。
    將所有邏輯整合到一個程序中，以根除所有子程序和匯入問題。
    """
    # 透過環境變數判斷是否在模擬測試中
    is_simulation = os.getenv("SIMULATION_MODE") == "true"
    base_path = Path.cwd() / "mock_content" if is_simulation else Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    # --- 步驟 1 & 2: 下載程式碼 ---
    try:
        if is_simulation:
            # 在模擬模式中，手動建立假的專案
            scripts_dir = project_path / "scripts"
            scripts_dir.mkdir(parents=True, exist_ok=True)
            (project_path / "requirements.txt").write_text("psutil\npytz\nfastapi\nuvicorn")
            (project_path / "main.py").write_text('import time\nprint("Uvicorn running on http://0.0.0.0:8000")\ntime.sleep(10)')
            print("✅ [SIM] 專案模擬建立完成。")
        else:
            from IPython.display import clear_output
            clear_output(wait=True)
            if FORCE_REPO_REFRESH and project_path.exists():
                subprocess.run(["sudo", "rm", "-rf", str(project_path)], check=True)
            base_path.mkdir(exist_ok=True)
            if not project_path.exists():
                git_command = ["git", "clone", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", REPOSITORY_URL, str(project_path)]
                subprocess.run(git_command, check=True)
                print("✅ 程式碼成功下載！")

        # --- 步驟 3: 設定環境並安裝依賴 ---
        os.chdir(project_path)
        print(f"✅ 工作目錄: {os.getcwd()}")
        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            # 確保所有 Colab 環境的核心依賴都被安裝
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psutil", "pytz", "IPython"], check=True)
            # 現在才安裝 requirements.txt 中的其他內容
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_path)], check=True)
            print("✅ 核心及專案依賴安裝完成。")
        else:
            print("⚠️ 找不到 requirements.txt")

    except Exception as e:
        print(f"💥 環境準備階段發生錯誤: {e}")
        return

    # ==========================================================================
    #  Part 2: 核心類別定義 (直接從 colab_run.py 整合進來)
    # ==========================================================================
    try:
        import psutil
        import pytz
        from IPython.display import clear_output
        # 在模擬模式中，偽造 google.colab
        if is_simulation:
            class FakeColabOutput:
                def eval_js(self, code): return "https://abcdef-1234.colab.googleusercontent.com/"
            class FakeGoogle:
                class colab: output = FakeColabOutput()
            sys.modules['google.colab'] = FakeGoogle.colab
            sys.modules['google.colab.output'] = FakeGoogle.colab.output
        from google.colab import output as colab_output
    except ImportError as e:
        print(f"💥 核心套件匯入失敗: {e}")
        return

    class LogManager:
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
            with self._lock: self._logs.append(log_item)
        def get_recent_logs(self, count: int) -> list:
            with self._lock: return list(self._logs)[-count:]

    class DisplayManager:
        def __init__(self, stats: dict, log_manager: LogManager, log_lines_to_show: int, lock: threading.Lock, refresh_rate: float):
            self._stats, self._log_manager, self._log_lines_to_show, self._refresh_rate, self._lock = stats, log_manager, log_lines_to_show, refresh_rate, lock
            self._stop_event, self._thread = threading.Event(), threading.Thread(target=self._run, daemon=True)
        def _run(self):
            while not self._stop_event.is_set():
                try:
                    clear_output(wait=True)
                    print("="*77 + "\n                      🚀 鳳凰之心指揮中心 v12 🚀\n" + "="*77)
                    recent_logs = self._log_manager.get_recent_logs(self._log_lines_to_show)
                    for log in recent_logs: print(f"[{log['timestamp'].strftime('%H:%M:%S')}] [{log['level']}] {log['message']}")
                    with self._lock: app_url = self._stats.get("app_url", "啟動中...")
                    print(f"\n🚀 開啟網頁介面 -> {app_url}\n" + "="*77)
                    time.sleep(self._refresh_rate)
                except Exception: pass
        def start(self): self._thread.start()
        def stop(self): self._stop_event.set()

    # ==========================================================================
    #  Part 3: 主要業務邏輯 (直接整合)
    # ==========================================================================
    def start_web_server(log_manager, stats, lock, port=8000):
        def get_colab_url(port):
            try: return colab_output.eval_js(f'google.colab.kernel.proxyPort({port})')
            except Exception: return None
        def server_thread():
            server_process = subprocess.Popen([sys.executable, "main.py"], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            for line in iter(server_process.stdout.readline, ''):
                log_manager.log("SERVER", line.strip())
                if "Uvicorn running on" in line:
                    log_manager.log("SUCCESS", "FastAPI 伺服器已成功啟動！正在獲取公開 URL...")
                    url = get_colab_url(port)
                    with lock: stats["app_url"] = url if url else "獲取 URL 失敗"
                    log_manager.log("SUCCESS", f"網頁介面 URL: {stats['app_url']}")
                    break
        threading.Thread(target=server_thread, daemon=True).start()

    def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path, refresh_rate):
        stats, lock = {"app_url": "等待伺服器啟動..."}, threading.Lock()
        log_manager = LogManager(timezone_str=timezone)
        display_manager = DisplayManager(stats, log_manager, log_lines, lock, refresh_rate)
        display_manager.start()
        log_manager.log("INFO", "視覺指揮官已啟動。")
        start_web_server(log_manager, stats, lock, port=8000)
        try:
            while True: time.sleep(1)
        except KeyboardInterrupt:
            log_manager.log("WARNING", "系統被手動中斷！")
        finally:
            display_manager.stop()
            print("--- 鳳凰之心指揮中心程序已結束 ---")

    # ==========================================================================
    #  Part 4: 最終執行
    # ==========================================================================
    run_phoenix_heart(
        log_lines=LOG_DISPLAY_LINES,
        archive_folder_name=LOG_ARCHIVE_FOLDER_NAME,
        timezone=TIMEZONE,
        project_path=project_path,
        base_path=base_path,
        refresh_rate=REFRESH_RATE_SECONDS
    )

# --- 執行啟動程序 ---
ultimate_bootstrap()
