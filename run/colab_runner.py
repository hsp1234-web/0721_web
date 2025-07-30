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
TARGET_BRANCH_OR_TAG = "6.1.3" #@param {type:"string"}
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
#@markdown **快速測試模式 (FAST_TEST_MODE)**
#@markdown > 預設開啟。將跳過所有 App 的依賴安裝和啟動，用於快速驗證核心通訊流程。
FAST_TEST_MODE = True #@param {type:"boolean"}

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
        log_file_path = project_path / "logs" / "launch.log"
        log_file_path.parent.mkdir(exist_ok=True)

        with open(log_file_path, "w") as f:
            process = subprocess.Popen(
                [sys.executable, str(project_path / "launch.py")],
                cwd=project_path,
                stdout=f,
                stderr=subprocess.STDOUT
            )

        with status_lock:
            shared_status["launch_process"] = process

        update_status(log=f"✅ 後端服務 (launch.py) 已啟動 (PID: {process.pid})。")
        update_status(task="後端服務運行中...")

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

def render_dashboard_html():
    """根據共享狀態和資料庫狀態生成儀表板的 HTML"""
    with status_lock:
        current_task = shared_status['current_task']
        logs = list(shared_status['logs'])
        db_status = shared_status.get('db_status')
        worker_error = shared_status.get('worker_error')

    # --- CSS ---
    css = "<style> body { background-color: #1a1a1a; color: #e0e0e0; font-family: 'Noto Sans TC', 'Fira Code', monospace; } .container { padding: 1em; } .panel { border: 1px solid #444; margin-bottom: 1em; } .title { font-weight: bold; padding: 0.5em; border-bottom: 1px solid #444; background-color: #2a2a2a;} .content { padding: 0.5em; } .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 1em; } .log { font-size: 0.9em; } .error { color: #ff6b6b; } .footer { text-align: center; padding-top: 1em; border-top: 1px solid #444; font-size: 0.8em; color: #888;} table { width: 100%;} </style>"

    # --- HTML Body ---
    stage, apps_status, action_url, cpu, ram = "未知", {}, None, 0, 0
    if db_status:
        stage, apps_status_json, action_url, cpu, ram = db_status
        apps_status = json.loads(apps_status_json) if apps_status_json else {}

    app_rows = ""
    status_map = {"running": "🟢 運行中", "pending": "🟡 等待中", "installing": "🛠️ 安裝中", "starting": "🚀 啟動中", "failed": "🔴 失敗"}
    for app, status in apps_status.items():
        app_rows += f"<tr><td>{app.capitalize()}</td><td>{status_map.get(status, f'❓ {status}')}</td></tr>"

    log_entries = "<br>".join(logs)

    footer_text = f"指揮中心前端任務: {current_task}"
    if worker_error:
        footer_text = f"<span class='error'>錯誤: {worker_error}</span>"
    elif action_url:
        footer_text = f'✅ 服務啟動完成！操作儀表板: <a href="{action_url}" target="_blank" style="color: #50fa7b;">{action_url}</a>'

    html = f"""
    <div class="container">
        <div class="grid">
            <div>
                <div class="panel"><div class="title">微服務狀態</div><div class="content"><table>{app_rows or '<tr><td>等待後端啟動...</td></tr>'}</table></div></div>
                <div class="panel"><div class="title">系統資源 (由後端回報)</div><div class="content"><table><tr><td>CPU</td><td>{cpu or 0.0:.1f}%</td></tr><tr><td>RAM</td><td>{ram or 0.0:.1f}%</td></tr></table></div></div>
            </div>
            <div class="panel"><div class="title">啟動程序日誌</div><div class="content log">{log_entries or '等待日誌...'}</div></div>
        </div>
        <div class.footer">{footer_text}</div>
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
    update_status(log="指揮中心 V16 啟動。")
    worker_thread = threading.Thread(target=background_worker)
    worker_thread.start()

    db_file = None
    last_displayed_html = ""
    launch_process_local = None

    try:
        while worker_thread.is_alive() or (shared_status.get("launch_process") and shared_status.get("launch_process").poll() is None):
            with status_lock:
                project_path = shared_status.get("project_path")
                launch_process_local = shared_status.get("launch_process")

            if project_path:
                db_file = project_path / "state.db"
                if db_file.exists():
                    try:
                        conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
                        cursor = conn.cursor()
                        cursor.execute("SELECT current_stage, apps_status, action_url, cpu_usage, ram_usage FROM status_table WHERE id = 1")
                        db_row = cursor.fetchone()
                        conn.close()
                        with status_lock:
                            shared_status["db_status"] = db_row
                    except sqlite3.OperationalError:
                        pass

            current_html = render_dashboard_html()
            if current_html != last_displayed_html:
                clear_output(wait=True)
                display(HTML(current_html))
                last_displayed_html = current_html

            time.sleep(REFRESH_RATE_SECONDS)

            if shared_status["worker_error"]:
                break

    except KeyboardInterrupt:
        update_status(task="偵測到手動中斷", log="🛑 正在準備終止程序...")
    finally:
        update_status(task="執行最終清理", log="正在終止所有背景程序...")

        if launch_process_local:
            launch_process_local.terminate()
            try:
                # 等待 launch.py 的 finally 區塊執行完畢 (生成報告)
                launch_process_local.wait(timeout=10)
                update_status(log="✅ 後端服務已成功終止。")
            except subprocess.TimeoutExpired:
                update_status(log="⚠️ 後端服務未能及時回應，將強制終結。")
                launch_process_local.kill()

        # 確保背景工作執行緒也結束
        worker_thread.join(timeout=5)

        # 最後執行歸檔
        project_path = shared_status.get("project_path")
        if project_path:
            archive_reports(project_path, LOG_ARCHIVE_FOLDER_NAME, TIMEZONE)

        update_status(task="所有程序已結束。")
        # 最後再渲染一次，顯示最終狀態
        clear_output(wait=True)
        display(HTML(render_dashboard_html()))


if __name__ == "__main__":
    main()
