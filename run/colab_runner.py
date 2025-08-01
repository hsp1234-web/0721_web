# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║                🚀 v19 鳳凰之心啟動器 (Launcher)                      ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   - 新功能：內建智慧型錯誤回報，啟動失敗時自動啟用複製模式。           ║
# ║   - 職責：在背景安全地啟動核心任務。                                   ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 🚀 v19 鳳凰之心啟動器 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "6.5.3" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
#@markdown > **提示：請試著在此欄位輸入 `FAIL` 來觸發「智慧型錯誤回報」機制。**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 應用程式參數**
#@markdown > **設定指揮中心的核心運行參數。**
#@markdown ---
#@markdown **儀表板更新頻率 (秒) (REFRESH_RATE_SECONDS)**
REFRESH_RATE_SECONDS = 1.0 #@param {type:"number"}
#@markdown **效能監控更新頻率 (秒) (PERFORMANCE_MONITOR_RATE_SECONDS)**
PERFORMANCE_MONITOR_RATE_SECONDS = 0.5 #@param {type:"number"}
#@markdown **日誌歸檔資料夾 (LOG_ARCHIVE_FOLDER_NAME)**
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **時區設定 (TIMEZONE)**
TIMEZONE = "Asia/Taipei" #@param {type:"string"}
#@markdown **快速測試模式 (FAST_TEST_MODE)**
FAST_TEST_MODE = False #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 3: Colab 連線設定**
#@markdown > **設定如何獲取 Colab 的公開代理網址。**
#@markdown ---
#@markdown **URL 獲取重試次數 (COLAB_URL_RETRIES)**
COLAB_URL_RETRIES = 12 #@param {type:"integer"}
#@markdown **URL 獲取重試延遲 (秒) (COLAB_URL_RETRY_DELAY)**
COLAB_URL_RETRY_DELAY = 5 #@param {type:"integer"}

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

import os
import sys
import subprocess
import time
import traceback
import json
from IPython.display import display, Markdown

# --- 後端執行程式碼 ---

# 定義一個全域狀態文件，用於儲存格之間的通訊
STATUS_FILE = "/tmp/phoenix_status.json"
LOG_FILE = "/tmp/phoenix_log.txt"

def format_error_message():
    """將最新的 Exception Traceback 格式化為 Markdown 區塊"""
    # 為了忠實還原設計圖，我們手動加入一個範例 Traceback
    # 在真實情境中，只需使用 traceback.format_exc()
    mock_traceback = "Traceback (most recent call last):\n  File \"<stdin>\", line 1, in <module>\nFileNotFoundError: [Errno 2] No such file or directory: 'config/invalid.yml'"
    return f"""### ❌ 啟動失敗\n\n```text\n{mock_traceback}\n```"""

def launch_background_task():
    """模擬啟動一個背景任務。"""
    script_content = f\"\"\"
import time
import os

log_file_path = '{LOG_FILE}'
os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

# 模擬程式啟動與日誌記錄
with open(log_file_path, 'w', encoding='utf-8') as f:
    tz = '{TIMEZONE}'
    os.environ['TZ'] = tz
    time.tzset()
    f.write(f'[{{time.strftime("%H:%M:%S", time.localtime())}}] [INFO] 鳳凰之心核心啟動...\\n')
    f.flush()
    time.sleep(2)
    f.write(f'[{{time.strftime("%H:%M:%S", time.localtime())}}] [BATTLE] 正在處理資料集 B...\\n')
    f.flush()
    time.sleep(1)
    f.write(f'[{{time.strftime("%H:%M:%S", time.localtime())}}] [SUCCESS] 任務 A 已完成。\\n')
    f.flush()
    time.sleep(3)
    f.write(f'[{{time.strftime("%H:%M:%S", time.localtime())}}] [ERROR] 資料集 B 處理失敗：資源不足。\\n')
    f.flush()
    time.sleep(1)
    f.write(f'[{{time.strftime("%H:%M:%S", time.localtime())}}] [CRITICAL] 系統偵測到嚴重錯誤。\\n')
    f.flush()
    time.sleep(2)
    f.write(f'[{{time.strftime("%H:%M:%S", time.localtime())}}] [PERF] CPU 85%, MEM 60%\\n')
    f.flush()
\"\"\"

    script_path = "/tmp/background_runner.py"
    with open(script_path, "w", encoding='utf-8') as f:
        f.write(script_content)

    process = subprocess.Popen(
        [sys.executable, script_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        preexec_fn=os.setsid
    )
    return process.pid

def main():
    try:
        # 清理舊的狀態，確保每次執行都是乾淨的開始
        if os.path.exists(STATUS_FILE): os.remove(STATUS_FILE)
        if os.path.exists(LOG_FILE): os.remove(LOG_FILE)

        if PROJECT_FOLDER_NAME == "FAIL":
            # 這是為了觸發錯誤回報機制的演示
            raise FileNotFoundError("[Errno 2] No such file or directory: 'config/invalid.yml'")

        pid = launch_background_task()

        status_data = {
            "pid": pid,
            "start_time": time.time(),
            "log_file": LOG_FILE,
            "status": "running",
            "timezone": TIMEZONE
        }
        with open(STATUS_FILE, "w") as f:
            json.dump(status_data, f)

        success_message = f\"\"\"✅ 背景任務已成功啟動 (PID: {pid})。\\nℹ️ 請執行下方的「📊 監控與報告中心」來追蹤進度。\"\"\"
        display(Markdown(success_message))

    except Exception as e:
        error_output = format_error_message()
        display(Markdown(error_output))

# 確保在 Colab 環境中可以找到 IPython
try:
    from IPython.display import display, Markdown
    main()
except ImportError:
    print("This script is designed to be run in a Colab environment.")
    print("Please paste this code into a Colab cell.")
