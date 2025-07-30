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

def render_dashboard_html():
    """生成包含動態更新邏輯的儀表板 HTML 骨架"""
    # 將 REFRESH_RATE_SECONDS 轉換為毫秒給 JS 使用
    refresh_interval_ms = int(REFRESH_RATE_SECONDS * 1000)

    css = """
    <style>
        body { background-color: #1a1a1a; color: #e0e0e0; font-family: 'Noto Sans TC', 'Fira Code', monospace; }
        .container { padding: 1em; }
        .panel { border: 1px solid #444; margin-bottom: 1em; }
        .title { font-weight: bold; padding: 0.5em; border-bottom: 1px solid #444; background-color: #2a2a2a;}
        .content { padding: 0.5em; }
        .grid { display: grid; grid-template-columns: 1fr 2fr; gap: 1em; }
        .log { font-size: 0.9em; white-space: pre-wrap; word-break: break-all; }
        .error { color: #ff6b6b; }
        .footer { text-align: center; padding-top: 1em; border-top: 1px solid #444; font-size: 0.8em; color: #888;}
        table { width: 100%;}
        .log-entry { margin-bottom: 5px; }
        .log-level-BATTLE { color: #82aaff; }
        .log-level-SUCCESS { color: #c3e88d; }
        .log-level-ERROR, .log-level-CRITICAL { color: #ff5370; }
        .log-level-INFO { color: #89ddff; }
        .log-level-WARN { color: #ffcb6b; }
    </style>
    """

    html_body = """
    <div class="container">
        <div class="grid">
            <div>
                <div class="panel">
                    <div class="title">微服務狀態</div>
                    <div class="content"><table id="app-status-table"><tbody><tr><td>等待後端回報...</td></tr></tbody></table></div>
                </div>
                <div class="panel">
                    <div class="title">系統資源 (由後端回報)</div>
                    <div class="content">
                        <table>
                            <tr><td>CPU</td><td id="cpu-usage">0.0%</td></tr>
                            <tr><td>RAM</td><td id="ram-usage">0.0%</td></tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="panel">
                <div class="title">啟動程序日誌</div>
                <div class="content log" id="log-container">等待日誌...</div>
            </div>
        </div>
        <div class="footer" id="footer-status">指揮中心前端任務: 初始化中...</div>
    </div>
    """

    javascript = f"""
    <script type="text/javascript">
        const statusMap = {{
            "running": "🟢 運行中", "pending": "🟡 等待中",
            "installing": "🛠️ 安裝中", "starting": "🚀 啟動中",
            "failed": "🔴 失敗", "unknown": "❓ 未知"
        }};
        const apiUrl = 'http://localhost:8088/api/v1/status';

        function updateDashboard() {{
            fetch(apiUrl)
                .then(response => {{
                    if (!response.ok) {{
                        throw new Error('後端服務尚未就緒...');
                    }}
                    return response.json();
                }})
                .then(data => {{
                    // 更新系統資源
                    document.getElementById('cpu-usage').textContent = `${{data.status.cpu_usage ? data.status.cpu_usage.toFixed(1) : '0.0'}}%`;
                    document.getElementById('ram-usage').textContent = `${{data.status.ram_usage ? data.status.ram_usage.toFixed(1) : '0.0'}}%`;

                    // 更新微服務狀態
                    const appStatusTable = document.getElementById('app-status-table').querySelector('tbody');
                    let apps = {{}};
                    try {{
                        apps = JSON.parse(data.status.apps_status || '{{}}');
                    }} catch(e) {{}}

                    let appRows = '';
                    if (Object.keys(apps).length > 0) {{
                        for (const [appName, status] of Object.entries(apps)) {{
                            const statusText = statusMap[status] || statusMap['unknown'];
                            appRows += `<tr><td>${{appName.charAt(0).toUpperCase() + appName.slice(1)}}</td><td>${{statusText}}</td></tr>`;
                        }}
                    }} else {{
                        appRows = '<tr><td>等待後端回報...</td></tr>';
                    }}
                    appStatusTable.innerHTML = appRows;

                    // 更新日誌
                    const logContainer = document.getElementById('log-container');
                    let logEntries = '';
                    if (data.logs && data.logs.length > 0) {{
                        // 日誌是從新到舊的，我們顯示時要反轉
                        data.logs.reverse().forEach(log => {{
                            const time = new Date(log.timestamp).toLocaleTimeString('en-GB');
                            logEntries += `<div class="log-entry"><span class="log-level-${{log.level}}">[${{time}}] [${{log.level}}]</span> ${{log.message}}</div>`;
                        }});
                    }} else {{
                        logEntries = '等待日誌...';
                    }}
                    logContainer.innerHTML = logEntries;

                    // 更新頁腳狀態
                    const footer = document.getElementById('footer-status');
                    if (data.status.action_url) {{
                        footer.innerHTML = `✅ 服務啟動完成！操作儀表板: <a href="${{data.status.action_url}}" target="_blank" style="color: #50fa7b;">${{data.status.action_url}}</a>`;
                    }} else {{
                        footer.textContent = `指揮中心後端任務: ${{data.status.current_stage || '執行中...'}}`;
                    }}
                }})
                .catch(error => {{
                    const footer = document.getElementById('footer-status');
                    footer.textContent = `前端狀態: ${{error.message}}`;
                }});
        }}

        // 立即執行一次，然後設定定時器
        updateDashboard();
        setInterval(updateDashboard, {refresh_interval_ms});
    </script>
    """
    return css + html_body + javascript

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
    update_status(log="指揮中心 V17 (API驅動版) 啟動。")

    # 顯示靜態的儀表板骨架，JS 將負責後續所有更新
    clear_output(wait=True)
    display(HTML(render_dashboard_html()))

    worker_thread = threading.Thread(target=background_worker)
    worker_thread.start()

    launch_process_local = None
    try:
        # 主執行緒現在的任務簡化為：等待背景程序結束
        # 我們仍然需要一個迴圈來獲取 launch_process 的控制代碼
        while not launch_process_local:
            with status_lock:
                launch_process_local = shared_status.get("launch_process")
                worker_error = shared_status.get("worker_error")
            if worker_error:
                # 如果背景工作出錯，直接跳出
                raise RuntimeError(f"背景工作執行緒出錯: {worker_error}")
            if not worker_thread.is_alive() and not launch_process_local:
                # 背景工作結束了，但沒有啟動任何程序
                raise RuntimeError("背景工作執行緒結束，但未能啟動後端服務。")
            time.sleep(0.5)

        # 等待後端服務程序執行結束
        launch_process_local.wait()

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

        update_status(task="所有程序已結束。")
        # 最後的日誌和狀態將由JS的最後一次API呼叫來更新，這裡不需要再渲染。
        # 我們只打印一個最終訊息。
        print(f"\n[{datetime.now(pytz.timezone(TIMEZONE)).strftime('%H:%M:%S')}] 指揮中心前端任務: 所有程序已結束。")


if __name__ == "__main__":
    main()
