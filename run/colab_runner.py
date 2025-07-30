# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║      🚀 Colab HTML 指揮中心 V16 (即時反饋版)                       ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   採用背景執行緒處理耗時任務，主執行緒負責高頻渲染，實現零延遲啟動。 ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心指揮中心 V16 (即時反饋版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "6.1.4" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 應用程式參數**
#@markdown > **設定指揮中心的核心運行參數。**
#@markdown ---
#@markdown **儀表板更新頻率 (秒) (REFRESH_RATE_SECONDS)**
REFRESH_RATE_SECONDS = 0.5 #@param {type:"number"}
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
LOG_DISPLAY_LINES = 20 #@param {type:"integer"}
#@markdown **最小重繪間隔 (秒) (MIN_REDRAW_INTERVAL_SECONDS)**
#@markdown > **這是為了防止日誌過於頻繁刷新導致閃爍，建議值為 1.0-2.0**
MIN_REDRAW_INTERVAL_SECONDS = 1.5 #@param {type:"number"}
#@markdown **日誌歸檔資料夾 (LOG_ARCHIVE_FOLDER_NAME)**
#@markdown > **留空即關閉歸檔功能。**
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **時區設定 (TIMEZONE)**
TIMEZONE = "Asia/Taipei" #@param {type:"string"}
#@markdown **快速測試模式 (FAST_TEST_MODE)**
#@markdown > 預設開啟。將跳過所有 App 的依賴安裝和啟動，用於快速驗證核心通訊流程。
FAST_TEST_MODE = True #@param {type:"boolean"}
#@markdown **使用模擬後端 (USE_MOCK_BACKEND)**
#@markdown > **推薦開啟以進行前端調試。** 將使用一個模擬的後端程式，而不是真實的 `launch.py`。
USE_MOCK_BACKEND = True #@param {type:"boolean"}

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
import sqlite3
import json
from IPython.display import display, HTML, clear_output
import pytz
from datetime import datetime
import threading
from collections import deque

# --- 共享狀態 ---
shared_status = {
    "current_task": "初始化中...",
    "logs": deque(maxlen=LOG_DISPLAY_LINES),
    "db_status": None,
    "worker_finished": False,
    "worker_error": None,
    "launch_process": None,
    "project_path": None,
}
status_lock = threading.Lock()

def update_status(task=None, log=None):
    """安全地更新共享狀態"""
    with status_lock:
        if task is not None:
            shared_status["current_task"] = task
        if log is not None:
            shared_status["logs"].append(f"[{datetime.now(pytz.timezone(TIMEZONE)).strftime('%H:%M:%S')}] {log}")

def background_worker():
    """在背景執行緒中處理所有耗時任務"""
    project_path = None
    try:
        base_path = Path("/content")
        project_path = base_path / PROJECT_FOLDER_NAME
        with status_lock:
            shared_status["project_path"] = project_path

        # --- 步驟 1: 準備專案環境 ---
        update_status(task="準備專案環境")
        if FORCE_REPO_REFRESH and project_path.exists():
            update_status(log=f"偵測到強制刷新，正在刪除舊的專案資料夾...")
            shutil.rmtree(project_path)
            update_status(log="✅ 舊資料夾已刪除。")

        if not project_path.exists():
            update_status(log=f"正在從 Github 下載程式碼...")
            process = subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", TARGET_BRANCH_OR_TAG, REPOSITORY_URL, str(project_path)],
                capture_output=True, text=True
            )
            if process.returncode != 0:
                raise RuntimeError(f"Git clone 失敗: {process.stderr}")
            update_status(log="✅ 程式碼下載成功。")
        else:
            update_status(log="專案資料夾已存在，跳過下載。")

        # --- 步驟 2: 生成設定檔 ---
        update_status(task="生成專案設定檔")
        config_data = {
            "REFRESH_RATE_SECONDS": REFRESH_RATE_SECONDS,
            "LOG_DISPLAY_LINES": LOG_DISPLAY_LINES,
            "LOG_ARCHIVE_FOLDER_NAME": LOG_ARCHIVE_FOLDER_NAME,
            "TIMEZONE": TIMEZONE,
            "FAST_TEST_MODE": FAST_TEST_MODE
        }
        config_file = project_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        update_status(log=f"✅ 設定檔已生成。")

        # --- 步驟 3: 觸發背景服務啟動程序 ---
        update_status(task="啟動後端服務")

        db_file_path = project_path / "state.db"
        log_file_path = project_path / "logs" / "backend.log"
        log_file_path.parent.mkdir(exist_ok=True)

        if USE_MOCK_BACKEND:
            update_status(log="🚀 使用模擬後端模式啟動...")
            backend_script_path = project_path / "mock_backend.py"
            # 將 mock_backend.py 複製到專案目錄中
            shutil.copy("mock_backend.py", backend_script_path)

            command = [
                sys.executable, str(backend_script_path),
                "--db-file", str(db_file_path),
                "--duration", "45"
            ]
            backend_name = "模擬後端 (mock_backend.py)"
        else:
            update_status(log="🚀 使用真實後端模式啟動...")
            command = [
                sys.executable, str(project_path / "launch.py"),
                "--db-file", str(db_file_path)
            ]
            backend_name = "真實後端 (launch.py)"

        with open(log_file_path, "w") as f:
            process = subprocess.Popen(command, cwd=project_path, stdout=f, stderr=subprocess.STDOUT)

        with status_lock:
            shared_status["launch_process"] = process

        update_status(log=f"✅ {backend_name} 已啟動 (PID: {process.pid})。")
        update_status(task=f"{backend_name} 運行中...")

    except Exception as e:
        error_message = f"❌ {e}"
        update_status(task="背景任務發生致命錯誤", log=error_message)
        with status_lock:
            shared_status["worker_error"] = str(e)
    finally:
        with status_lock:
            shared_status["worker_finished"] = True
            if not shared_status.get("launch_process"):
                update_status(task="背景任務提前終止")

def render_dashboard_html(status_data, logs_buffer):
    """根據傳入的狀態和日誌緩衝區生成儀表板的 HTML"""
    # --- CSS ---
    css = "<style> body { background-color: #1a1a1a; color: #e0e0e0; font-family: 'Noto Sans TC', 'Fira Code', monospace; } .container { padding: 1em; } .panel { border: 1px solid #444; margin-bottom: 1em; } .title { font-weight: bold; padding: 0.5em; border-bottom: 1px solid #444; background-color: #2a2a2a;} .content { padding: 0.5em; } .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 1em; } .log { font-size: 0.9em; white-space: pre-wrap; word-break: break-all; } .error { color: #ff6b6b; } .footer { text-align: center; padding-top: 1em; border-top: 1px solid #444; font-size: 0.8em; color: #888;} table { width: 100%;} </style>"

    # --- HTML Body ---
    stage, apps_status, action_url, cpu, ram = "等待後端回報...", {}, None, 0.0, 0.0
    if status_data:
        stage = status_data.get('current_stage', stage)
        apps_status_json = status_data.get('apps_status')
        action_url = status_data.get('action_url')
        cpu = status_data.get('cpu_usage', cpu)
        ram = status_data.get('ram_usage', ram)
        if apps_status_json:
            try:
                apps_status = json.loads(apps_status_json)
            except json.JSONDecodeError:
                apps_status = {}

    app_rows = ""
    status_map = {"running": "🟢 運行中", "pending": "🟡 等待中", "installing": "🛠️ 安裝中", "starting": "🚀 啟動中", "failed": "🔴 失敗"}
    if apps_status:
        for app, status in apps_status.items():
            app_rows += f"<tr><td>{app.capitalize()}</td><td>{status_map.get(status, f'❓ {status}')}</td></tr>"
    else:
        app_rows = '<tr><td>等待後端回報...</td></tr>'


    log_entries = "<br>".join(logs_buffer) if logs_buffer else "等待日誌..."

    # 從共享狀態獲取前端的任務狀態
    with status_lock:
        current_task = shared_status['current_task']
        worker_error = shared_status.get('worker_error')

    footer_text = f"指揮中心前端任務: {current_task}"
    if worker_error:
        footer_text = f"<span class='error'>錯誤: {worker_error}</span>"
    elif action_url:
        footer_text = f'✅ 服務啟動完成！操作儀表板: <a href="{action_url}" target="_blank" style="color: #50fa7b;">{action_url}</a>'
    else:
        footer_text = f"指揮中心後端任務: {stage}"


    html = f"""
    <div class="container">
        <div class="grid">
            <div>
                <div class="panel"><div class="title">微服務狀態</div><div class="content"><table><tbody>{app_rows}</tbody></table></div></div>
                <div class="panel"><div class="title">系統資源 (由後端回報)</div><div class="content"><table><tr><td>CPU</td><td>{cpu or 0.0:.1f}%</td></tr><tr><td>RAM</td><td>{ram or 0.0:.1f}%</td></tr></table></div></div>
            </div>
            <div class="panel"><div class="title">啟動程序日誌</div><div class="content log">{log_entries}</div></div>
        </div>
        <div class="footer">{footer_text}</div>
    </div>
    """
    return css + html

def archive_reports(project_path, archive_folder_name, timezone_str):
    """將生成的報告歸檔到指定目錄"""
    if not archive_folder_name:
        update_status(log="ℹ️ 日誌歸檔功能已關閉。")
        return

    try:
        archive_base_path = Path("/content") / archive_folder_name
        archive_base_path.mkdir(exist_ok=True)

        tz = pytz.timezone(timezone_str)
        timestamp_folder_name = datetime.now(tz).isoformat()
        archive_target_path = archive_base_path / timestamp_folder_name
        archive_target_path.mkdir()

        source_reports_path = project_path / "logs"
        report_files = ["綜合戰情簡報.md", "效能分析報告.md", "詳細日誌報告.md"]

        update_status(task="歸檔報告", log=f"🗄️ 開始歸檔報告至: {archive_target_path}")
        for report_name in report_files:
            source_file = source_reports_path / report_name
            if source_file.exists():
                shutil.move(str(source_file), str(archive_target_path / report_name))
                update_status(log=f"  - 已移動: {report_name}")
            else:
                update_status(log=f"  - 警告: 找不到報告檔案 {report_name}")

        update_status(log="✅ 報告歸檔完成。")

    except Exception as e:
        update_status(log=f"❌ 歸檔報告時發生錯誤: {e}")

def main():
    update_status(log=f"指揮中心 V18 (低頻刷新版) 啟動。")

    worker_thread = threading.Thread(target=background_worker)
    worker_thread.start()

    launch_process_local = None
    db_file = None

    # 前端日誌緩衝區
    logs_buffer = deque(maxlen=LOG_DISPLAY_LINES)
    # 用於追蹤已顯示的日誌ID，避免重複
    displayed_log_ids = set()

    last_redraw_time = 0
    status_data = {}

    try:
        # 等待後端服務啟動
        while not launch_process_local:
            with status_lock:
                launch_process_local = shared_status.get("launch_process")
                project_path = shared_status.get("project_path")
                worker_error = shared_status.get("worker_error")
            if worker_error: raise RuntimeError(f"背景工作執行緒出錯: {worker_error}")
            if not worker_thread.is_alive() and not launch_process_local:
                raise RuntimeError("背景工作執行緒結束，但未能啟動後端服務。")
            time.sleep(0.5)

        db_file = project_path / "state.db"

        # 主渲染迴圈
        while launch_process_local.poll() is None:
            new_logs_found = False

            # 從資料庫獲取狀態和日誌
            try:
                if db_file.exists():
                    with sqlite3.connect(f"file:{db_file}?mode=ro", uri=True) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        # 獲取主狀態
                        cursor.execute("SELECT * FROM status_table WHERE id = 1")
                        row = cursor.fetchone()
                        if row:
                            status_data = dict(row)

                        # 獲取新的日誌
                        cursor.execute("SELECT id, timestamp, level, message FROM phoenix_logs WHERE id NOT IN ({seq}) ORDER BY id ASC".format(
                            seq=','.join(['?']*len(displayed_log_ids)) if displayed_log_ids else "''"
                        ), list(displayed_log_ids))

                        new_logs = cursor.fetchall()
                        if new_logs:
                            new_logs_found = True
                            for log_row in new_logs:
                                log_id, ts, level, msg = log_row
                                formatted_ts = datetime.fromisoformat(ts).strftime('%H:%M:%S')
                                logs_buffer.append(f"[{formatted_ts}] [{level}] {msg}")
                                displayed_log_ids.add(log_id)

            except sqlite3.OperationalError:
                # 資料庫可能正在寫入，暫時忽略
                time.sleep(0.1)
                continue

            # 判斷是否重繪
            time_since_last_redraw = time.time() - last_redraw_time
            # 條件：1. 有新日誌 且 2. 距離上次重繪已超過最小間隔
            #      或者 3. 狀態報告中的 action_url 首次出現 (表示任務完成)
            should_redraw = (new_logs_found and time_since_last_redraw > MIN_REDRAW_INTERVAL_SECONDS) or \
                            (status_data.get('action_url') and 'action_url_displayed' not in shared_status)

            if should_redraw:
                clear_output(wait=True)
                display(HTML(render_dashboard_html(status_data, logs_buffer)))
                last_redraw_time = time.time()
                if status_data.get('action_url'):
                    shared_status['action_url_displayed'] = True

            time.sleep(REFRESH_RATE_SECONDS)

    except (KeyboardInterrupt, RuntimeError) as e:
        if isinstance(e, KeyboardInterrupt):
            update_status(task="偵測到手動中斷", log="🛑 正在準備終止程序...")
        else:
            update_status(task="前端偵測到錯誤", log=f"❌ {e}")

    finally:
        # 重新從共享狀態獲取一次 launch_process，以防主迴圈未進入
        with status_lock:
            launch_process_local = shared_status.get("launch_process")

        update_status(task="執行最終清理", log="正在準備結束程序...")

        if launch_process_local and launch_process_local.poll() is None:
            update_status(log="偵測到後端服務仍在運行，正在嘗試正常終止...")
            launch_process_local.terminate()
            try:
                # 延長等待時間以確保報告能生成
                launch_process_local.wait(timeout=15)
                update_status(log="✅ 後端服務已成功終止。")
            except subprocess.TimeoutExpired:
                update_status(log="⚠️ 後端服務未能及時回應，將強制終結。")
                launch_process_local.kill()
        elif launch_process_local:
            update_status(log=f"✅ 後端服務已自行結束 (返回碼: {launch_process_local.poll()})。")

        # 確保背景工作執行緒也結束
        worker_thread.join(timeout=5)

        # 最後執行歸檔
        with status_lock:
            project_path = shared_status.get("project_path")
        if project_path:
            archive_reports(project_path, LOG_ARCHIVE_FOLDER_NAME, TIMEZONE)

        # 最後再渲染一次，確保顯示最終狀態
        clear_output(wait=True)
        display(HTML(render_dashboard_html(status_data, logs_buffer)))
        update_status(task="所有程序已結束。")
        print(f"\n[{datetime.now(pytz.timezone(TIMEZONE)).strftime('%H:%M:%S')}] 指揮中心前端任務: 所有程序已結束。")


if __name__ == "__main__":
    main()
