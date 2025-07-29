# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 混合模式啟動器 v3.0                                     ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       在 Colab 端提供輕量的文字動畫以緩解等待焦慮，在完成核心準備後， ║
# ║       將使用者無縫引導至功能完整的 Web UI 監控儀表板。               ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心啟動器 v3.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "4.1.2" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心邏輯
# ==============================================================================
import os
import sys
import shutil
import subprocess
from pathlib import Path
import time
import threading
from IPython.display import clear_output

class Spinner:
    """一個簡單的文字旋轉動畫類"""
    def __init__(self, message="處理中..."):
        self._message = message
        self._stop_event = threading.Event()
        self._thread = threading.Thread(target=self._spin, daemon=True)

    def _spin(self):
        spinner_chars = ['/', '-', '\\', '|']
        i = 0
        while not self._stop_event.is_set():
            sys.stdout.write(f'\r{spinner_chars[i % len(spinner_chars)]} {self._message}')
            sys.stdout.flush()
            time.sleep(0.1)
            i += 1

    def start(self):
        self._thread.start()

    def stop(self, final_message="完成！"):
        self._stop_event.set()
        self._thread.join(timeout=1)
        # 清除旋轉動畫並打印最終訊息
        sys.stdout.write(f'\r{"✅ " + final_message:<50}\n')
        sys.stdout.flush()

def run_task_with_spinner(task_func, message):
    """用一個旋轉動畫來執行一個耗時任務"""
    spinner = Spinner(message)
    spinner.start()
    try:
        task_func()
        spinner.stop()
    except Exception as e:
        spinner.stop(f"失敗！錯誤: {e}")
        raise

def main():
    clear_output(wait=True)
    print("🚀 鳳凰之心混合模式啟動程序...")
    print("="*80)

    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    # --- 步驟 1: 下載專案 ---
    def task_clone_repo():
        if FORCE_REPO_REFRESH and project_path.exists():
            shutil.rmtree(project_path)
        if not project_path.exists():
            git_command = ["git", "clone", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", "-q", REPOSITORY_URL, str(project_path)]
            subprocess.run(git_command, check=True, cwd=base_path)
    run_task_with_spinner(task_clone_repo, "正在準備並下載專案程式碼...")

    os.chdir(project_path)
    print(f"✅ 已切換至專案目錄: {os.getcwd()}")

    # --- 步驟 2: 安裝核心依賴 ---
    def task_install_deps():
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psutil", "pyyaml", "uv", "nest_asyncio", "httpx"], check=True)
    run_task_with_spinner(task_install_deps, "正在安裝 Colab 核心依賴...")

    # --- 步驟 3: 在背景啟動後端服務 ---
    print("\n✅ 核心環境準備就緒。")
    print("🚀 即將在背景啟動所有後端服務 (包括 Web 監控儀表板)...")

    # 使用 Popen 在背景啟動 launch.py，並將其輸出導向到一個日誌檔案
    log_file = open("launch_logs.txt", "w")
    subprocess.Popen([sys.executable, "launch.py"], stdout=log_file, stderr=subprocess.STDOUT)

    print("⏳ 等待 Web 儀表板服務上線 (約需 15 秒)...")
    time.sleep(15)

    # --- 步驟 4: 顯示最終連結 ---
    proxy_url = "http://localhost:8000"
    print("\n" + "="*80)
    print("🎉 啟動程序已觸發！ 🎉".center(80))
    print("\n")
    print(f"👉 請點擊以下連結，在新分頁中打開「即時監控儀表板」:")
    print(f"   {proxy_url}")
    print("\n")
    print("您可以在儀表板中觀察詳細的服務啟動進度。")
    print(f"所有詳細的背景日誌都記錄在專案資料夾的 `launch_logs.txt` 檔案中。")
    print("請注意：關閉此 Colab 執行環境將會終止所有後端服務。")
    print("="*80)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
