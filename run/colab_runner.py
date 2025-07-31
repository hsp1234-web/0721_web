# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║      🚀 Colab HTML 指揮中心 V18 (優雅關閉 & 中文化報告)              ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   V18 更新日誌:                                                      ║
# ║   - 實作優雅關閉機制，確保手動中斷時能完整生成報告。             ║
# ║   - 將最終產生的報告檔案名稱中文化。                             ║
# ║   - 修正 Colab 代理 URL 在特定環境下的生成錯誤。                   ║
# ║   - 更新 Colab 表單中的部分 UI 文字為繁體中文。                    ║
# ║                                                                      ║
# ║                                                                      ║
# ║   採用背景執行緒處理耗時任務，主執行緒負責高頻渲染，實現零延遲啟動。 ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

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
try:
    import yaml
except ImportError:
    # Colab 環境通常預裝了，但以防萬一
    print("正在安裝 PyYAML...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyyaml"])
    import yaml

#@title 💎 鳳凰之心指揮中心 V17 (趨勢圖版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "6.5.1" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
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
#@markdown > **建議小於等於儀表板更新頻率，以確保數據即時性。**
PERFORMANCE_MONITOR_RATE_SECONDS = 0.5 #@param {type:"number"}
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
LOG_DISPLAY_LINES = 50 #@param {type:"integer"}
#@markdown **日誌歸檔資料夾 (LOG_ARCHIVE_FOLDER_NAME)**
#@markdown > **留空即關閉歸檔功能。歸檔位置在 Colab 左側檔案總管的 `/content/<您指定的資料夾名稱>` 中。**
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **時區設定 (TIMEZONE)**
TIMEZONE = "Asia/Taipei" #@param {type:"string"}
#@markdown **快速測試模式 (FAST_TEST_MODE)**
#@markdown > 預設開啟。將跳過所有 App 的依賴安裝和啟動，用於快速驗證核心通訊流程。
FAST_TEST_MODE = False #@param {type:"boolean"}
#@markdown ---
#@markdown ### **Part 3: 日誌顯示設定**
#@markdown > **選擇您想在儀表板上看到的日誌等級。**
#@markdown **顯示戰鬥日誌 (SHOW_LOG_LEVEL_BATTLE)**
SHOW_LOG_LEVEL_BATTLE = True #@param {type:"boolean"}
#@markdown **顯示成功日誌 (SHOW_LOG_LEVEL_SUCCESS)**
SHOW_LOG_LEVEL_SUCCESS = True #@param {type:"boolean"}
#@markdown **顯示資訊日誌 (SHOW_LOG_LEVEL_INFO)**
SHOW_LOG_LEVEL_INFO = False #@param {type:"boolean"}
#@markdown **顯示命令日誌 (SHOW_LOG_LEVEL_CMD)**
SHOW_LOG_LEVEL_CMD = False #@param {type:"boolean"}
#@markdown **顯示系統日誌 (SHOW_LOG_LEVEL_SHELL)**
SHOW_LOG_LEVEL_SHELL = False #@param {type:"boolean"}
#@markdown **顯示錯誤日誌 (SHOW_LOG_LEVEL_ERROR)**
SHOW_LOG_LEVEL_ERROR = True #@param {type:"boolean"}
#@markdown **顯示嚴重錯誤日誌 (SHOW_LOG_LEVEL_CRITICAL)**
SHOW_LOG_LEVEL_CRITICAL = True #@param {type:"boolean"}
#@markdown **顯示效能日誌 (SHOW_LOG_LEVEL_PERF)**
SHOW_LOG_LEVEL_PERF = False #@param {type:"boolean"}
#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心邏輯
# ==============================================================================

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
            update_status(log="偵測到強制刷新，正在刪除舊的專案資料夾...")
            shutil.rmtree(project_path)
            update_status(log="✅ 舊資料夾已刪除。")

        if not project_path.exists():
            update_status(log="正在從 Github 下載程式碼...")
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
        log_levels_to_show = {
            "BATTLE": SHOW_LOG_LEVEL_BATTLE,
            "SUCCESS": SHOW_LOG_LEVEL_SUCCESS,
            "INFO": SHOW_LOG_LEVEL_INFO,
            "CMD": SHOW_LOG_LEVEL_CMD,
            "SHELL": SHOW_LOG_LEVEL_SHELL,
            "ERROR": SHOW_LOG_LEVEL_ERROR,
            "CRITICAL": SHOW_LOG_LEVEL_CRITICAL,
            "PERF": SHOW_LOG_LEVEL_PERF,
        }

        config_data = {
            "REFRESH_RATE_SECONDS": REFRESH_RATE_SECONDS,
            "PERFORMANCE_MONITOR_RATE_SECONDS": PERFORMANCE_MONITOR_RATE_SECONDS,
            "LOG_DISPLAY_LINES": LOG_DISPLAY_LINES,
            "LOG_ARCHIVE_FOLDER_NAME": LOG_ARCHIVE_FOLDER_NAME,
            "TIMEZONE": TIMEZONE,
            "FAST_TEST_MODE": FAST_TEST_MODE,
            "LOG_LEVELS_TO_SHOW": {level: show for level, show in log_levels_to_show.items() if show}
        }
        config_file = project_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f, indent=4, ensure_ascii=False)
        update_status(log="✅ Colab 設定檔 (config.json) 已生成。")

        # --- 步驟 2.5: 同步後端設定檔 ---
        update_status(task="同步後端設定檔")
        resource_settings_file = project_path / "config" / "resource_settings.yml"
        if resource_settings_file.exists():
            try:
                with open(resource_settings_file, 'r', encoding='utf-8') as f:
                    resource_settings = yaml.safe_load(f)

                # 更新設定值
                resource_settings['resource_monitoring']['monitor_refresh_seconds'] = REFRESH_RATE_SECONDS

                with open(resource_settings_file, 'w', encoding='utf-8') as f:
                    yaml.dump(resource_settings, f, allow_unicode=True)

                update_status(log=f"✅ 後端設定檔 (resource_settings.yml) 已同步更新頻率為 {REFRESH_RATE_SECONDS} 秒。")
            except Exception as e:
                update_status(log=f"⚠️ 無法更新後端設定檔: {e}")
        else:
            update_status(log="⚠️ 找不到後端資源設定檔，後端將使用預設更新頻率。")


        # --- 步驟 3: 觸發背景服務啟動程序 ---
        update_status(task="啟動後端服務")

        db_file_path = project_path / "state.db"
        log_file_path = project_path / "logs" / "backend.log"
        log_file_path.parent.mkdir(exist_ok=True)

        update_status(log="🚀 使用真實後端模式啟動...")
        command = [
            sys.executable, str(project_path / "scripts" / "launch.py"),
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
        #entry-point-panel {
            display: none; /* 預設隱藏 */
            grid-column: 1 / -1; /* 橫跨所有欄 */
            text-align: center;
            padding: 1em;
            background-color: #2d2d2d;
            border: 1px solid #50fa7b;
        }
        #entry-point-button {
            display: inline-block;
            padding: 10px 20px;
            font-size: 1.2em;
            font-weight: bold;
            color: #1a1a1a;
            background-color: #50fa7b;
            border: none;
            border-radius: 5px;
            text-decoration: none;
            cursor: pointer;
        }
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
                <div class="panel">
                    <div class="title">效能趨勢 (文字圖)</div>
                    <div class="content">
                        <table>
                            <tr><td>CPU</td><td id="cpu-trend">等待數據...</td></tr>
                            <tr><td>RAM</td><td id="ram-trend">等待數據...</td></tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="panel">
                <div class="title">啟動程序日誌</div>
                <div class="content log" id="log-container">等待日誌...</div>
            </div>
        </div>
        <div id="entry-point-panel">
             <a id="entry-point-button" href="#" target="_blank">🚀 進入主控台</a>
             <p style="font-size:0.9em; margin-top: 8px;">主儀表板已就緒，點擊上方按鈕進入操作介面。</p>
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

                    // 更新頁腳和主控台入口
                    const footer = document.getElementById('footer-status');
                    const entryPointPanel = document.getElementById('entry-point-panel');
                    const entryPointButton = document.getElementById('entry-point-button');

                    if (data.status.action_url) {{
                        // 當 URL 可用時，顯示主控台入口面板
                        entryPointPanel.style.display = 'block';
                        entryPointButton.href = data.status.action_url;
                        // 頁腳可以顯示最終狀態
                        footer.textContent = `指揮中心後端任務: ${{data.status.current_stage || '所有服務運行中'}}`;
                    }} else {{
                        // URL 不可用時，隱藏面板並在頁腳顯示進度
                        entryPointPanel.style.display = 'none';
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

def final_report_processing(project_path, archive_folder_name, timezone_str):
    """處理報告的重新命名、整合與歸檔"""
    if not project_path:
        return

    logs_dir = project_path / "logs"
    if not logs_dir.is_dir():
        update_status(log=f"⚠️ 找不到日誌目錄 {logs_dir}，跳過報告處理。")
        return

    # --- 1. 報告檔名中文化 ---
    update_status(task="報告中文化", log="正在將報告檔案重新命名為繁體中文...")
    rename_map = {
        "summary_report.md": "任務總結報告.md",
        "performance_report.md": "效能分析報告.md",
        "detailed_log_report.md": "詳細日誌報告.md"
    }
    renamed_files = []
    for old_name, new_name in rename_map.items():
        old_path = logs_dir / old_name
        new_path = logs_dir / new_name
        if old_path.exists():
            try:
                old_path.rename(new_path)
                update_status(log=f"  - 已重新命名: {old_name} -> {new_name}")
                renamed_files.append(new_name)
            except Exception as e:
                update_status(log=f"  - ❌ 重新命名失敗: {e}")
        else:
            update_status(log=f"  - 警告: 找不到原始報告檔案 {old_name}")

    # --- 2. 整合報告生成 ---
    update_status(task="生成整合報告", log="正在合併報告分卷...")
    try:
        # 使用已重新命名的中文檔案來生成整合報告
        consolidated_content = f"# 鳳凰之心最終任務報告\n\n**報告產生時間:** {datetime.now(pytz.timezone(timezone_str)).isoformat()}\n\n---\n\n"
        for report_file in renamed_files:
            report_path = logs_dir / report_file
            if report_path.exists():
                consolidated_content += f"## 原始報告: {report_file}\n\n"
                consolidated_content += report_path.read_text(encoding='utf-8')
                consolidated_content += "\n\n---\n\n"

        if len(consolidated_content) > 200:
            final_report_path = project_path / "最終運行報告.md" # 整合報告也使用中文名
            final_report_path.write_text(consolidated_content, encoding='utf-8')
            update_status(log="✅ 整合報告已生成: 最終運行報告.md")
        else:
            update_status(log="沒有足夠的報告分卷來生成整合報告。")
    except Exception as e:
        update_status(log=f"❌ 生成整合報告時發生錯誤: {e}")

    # --- 3. 歸檔 ---
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

        update_status(task="歸檔報告", log=f"🗄️ 開始歸檔報告至: {archive_target_path}")
        # 不再使用 glob，因為它對非 ASCII 字元的處理可能不可靠。
        # 改為使用我們在重新命名步驟中建立的 `renamed_files` 列表，這樣更穩健。
        files_to_archive = [logs_dir / f for f in renamed_files]
        for source_file in files_to_archive:
            if source_file.exists():
                shutil.move(str(source_file), str(archive_target_path / source_file.name))
                update_status(log=f"  - 已移動: {source_file.name}")
        update_status(log="✅ 報告歸檔完成。")
    except Exception as e:
        update_status(log=f"❌ 歸檔報告時發生錯誤: {e}")


def main():
    update_status(log="指揮中心 V17 (API驅動版) 啟動。")

    clear_output(wait=True)
    display(HTML(render_dashboard_html()))

    worker_thread = threading.Thread(target=background_worker)
    worker_thread.start()

    launch_process_local = None
    try:
        while not launch_process_local:
            with status_lock:
                launch_process_local = shared_status.get("launch_process")
                worker_error = shared_status.get("worker_error")
            if worker_error:
                raise RuntimeError(f"背景工作執行緒出錯: {worker_error}")
            if not worker_thread.is_alive() and not launch_process_local:
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
        with status_lock:
            launch_process_local = shared_status.get("launch_process")
            project_path = shared_status.get("project_path")

        update_status(task="執行最終清理", log="正在準備結束程序...")

        if launch_process_local and launch_process_local.poll() is None:
            update_status(log="偵測到後端服務仍在運行，正在嘗試正常終止 (SIGTERM)...")
            launch_process_local.terminate() # 發送 SIGTERM
            try:
                # 給予後端寬裕的時間(例如 15 秒)來處理關閉、生成報告
                update_status(log="給予後端 15 秒時間進行關機與報告生成...")
                launch_process_local.wait(timeout=15)
                update_status(log="✅ 後端服務已成功終止。")
            except subprocess.TimeoutExpired:
                update_status(log="⚠️ 後端服務未能及時回應，將強制終結 (SIGKILL)。")
                launch_process_local.kill()
        elif launch_process_local:
            update_status(log=f"✅ 後端服務已自行結束 (返回碼: {launch_process_local.poll()})。")

        # 確保背景工作執行緒也結束
        worker_thread.join(timeout=5)

        # 將報告處理邏輯統一到一個函式中
        final_report_processing(project_path, LOG_ARCHIVE_FOLDER_NAME, TIMEZONE)

        # 最後的日誌和狀態將由JS的最後一次API呼叫來更新，這裡不需要再渲染。
        # 我們只打印一個最終訊息。
        final_message = f"✅ [{datetime.now(pytz.timezone(TIMEZONE)).strftime('%H:%M:%S')}] 所有程序已順利結束。"
        print(f"\n{final_message}")

def run_main():
    """
    執行主函數並優雅地處理結束流程，以提供乾淨的 Colab 輸出。
    """
    try:
        main()
    except (KeyboardInterrupt, SystemExit) as e:
        # 如果是手動中斷或良性退出，我們不需要顯示任何錯誤。
        # 腳本的 finally 區塊已經處理了清理工作。
        # 我們可以在這裡印一個更明確的「手動停止」訊息。
        if isinstance(e, KeyboardInterrupt):
            print("\n🛑 操作已被使用者手動中斷。")
    except Exception as e:
        # 捕捉其他所有未預期的錯誤，並以更友好的方式顯示。
        print(f"\n❌ 發生未預期的錯誤: {e}")
        # 如果需要，可以在這裡顯示詳細的 traceback
        # import traceback
        # traceback.print_exc()
    finally:
        # 為了進一步抑制 IPython 的 "To exit" UserWarning，我們可以在這裡導入 warnings 並過濾它
        # 但通常讓腳本自然結束是最好的方法。
        pass


if __name__ == "__main__":
    run_main()
