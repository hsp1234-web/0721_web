# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║      🚀 Colab HTML 指揮中心 V19 (穩定版)                           ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   V19 更新日誌:                                                      ║
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
    import httpx
    from google.colab import output as colab_output
except ImportError:
    print("正在安裝指揮中心核心依賴 (PyYAML, httpx)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "pyyaml", "httpx"])
    import yaml
    import httpx
    from google.colab import output as colab_output

#@title 💎 鳳凰之心指揮中心 V19 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "6.5.3" #@param {type:"string"}
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
#@markdown ### **Part 4: Colab 連線設定**
#@markdown > **設定如何獲取 Colab 的公開代理網址。**
#@markdown ---
#@markdown **URL 獲取重試次數 (COLAB_URL_RETRIES)**
COLAB_URL_RETRIES = 12 #@param {type:"integer"}
#@markdown **URL 獲取重試延遲 (秒) (COLAB_URL_RETRY_DELAY)**
COLAB_URL_RETRY_DELAY = 5 #@param {type:"integer"}

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
            "LOG_LEVELS_TO_SHOW": {level: show for level, show in log_levels_to_show.items() if show},
            "COLAB_URL_RETRIES": COLAB_URL_RETRIES,
            "COLAB_URL_RETRY_DELAY": COLAB_URL_RETRY_DELAY,
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
        .colab-link-panel {
            display: none; /* 預設隱藏 */
            padding: 0.8em;
            margin-bottom: 1em;
            background-color: #2c3e50;
            border: 1px solid #3498db;
            border-radius: 5px;
            text-align: center;
            font-size: 1.1em;
        }
        .colab-link-panel strong {
            color: #ffffff;
        }
        .colab-link-panel a {
            color: #f1c40f;
            font-weight: bold;
            text-decoration: none;
        }
        .colab-link-panel a:hover {
            text-decoration: underline;
        }
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
        <div id="colab-link-container" class="colab-link-panel">
             🔗 <strong>Colab 代理連結:</strong> <a href="#" id="colab-proxy-link" target="_blank">正在生成中...</a>
        </div>
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
        <div id="entry-point-panel">
             <a id="entry-point-button" href="#" target="_blank">🚀 進入主控台</a>
             <p style="font-size:0.9em; margin-top: 8px;">主儀表板已就緒，點擊上方按鈕進入操作介面。</p>
        </div>
        <div class="footer" id="footer-status">指揮中心前端任務: 初始化中...</div>
    </div>
    """

    # 使用 .format() 方法，並對所有 JS 的大括號進行轉義 ({{ ... }})
    javascript = """
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
                    const colabLinkContainer = document.getElementById('colab-link-container');
                    const colabProxyLink = document.getElementById('colab-proxy-link');

                    if (data.status.action_url) {{
                        // --- 更新 Colab 代理連結 ---
                        colabLinkContainer.style.display = 'block';
                        colabProxyLink.href = data.status.action_url;
                        colabProxyLink.textContent = data.status.action_url;

                        // --- 更新舊的主控台入口 (保持相容) ---
                        entryPointPanel.style.display = 'block';
                        entryPointButton.href = data.status.action_url;

                        // 頁腳可以顯示最終狀態
                        footer.textContent = `指揮中心後端任務: ${{data.status.current_stage || '所有服務運行中'}}`;
                    }} else {{
                        // URL 不可用時，隱藏面板並在頁腳顯示進度
                        colabLinkContainer.style.display = 'none';
                        entryPointPanel.style.display = 'none';
                        footer.textContent = `指揮中心後端任務: ${{data.status.current_stage || '執行中...'}}`;
                    }}
                }})
                .catch(error => {{
                    const footer = document.getElementById('footer-status');
                    footer.textContent = `前端狀態: ${{error.message}}`;
                }});
        }}

        function triggerShutdown() {{
            if (confirm('您確定要關閉所有後端服務嗎？此操作將會終止所有執行中的任務。')) {{
                document.getElementById('shutdown-button').disabled = true;
                document.getElementById('shutdown-button').textContent = '正在發送關閉信號...';

                const shutdownUrl = 'http://localhost:8088/api/v1/shutdown';
                fetch(shutdownUrl, {{ method: 'POST' }})
                    .then(response => response.json())
                    .then(data => {{
                        console.log('Shutdown initiated:', data);
                        // 後續的狀態更新將由儀表板的常規輪詢來處理
                    }})
                    .catch(error => {{
                        console.error('Error triggering shutdown:', error);
                        alert('發送關閉信號失敗，請檢查後端日誌。');
                        document.getElementById('shutdown-button').disabled = false;
                        document.getElementById('shutdown-button').textContent = '🛑 手動關閉所有服務';
                    }});
            }}
        }}

        // 立即執行一次，然後設定定時器
        updateDashboard();
        setInterval(updateDashboard, {refresh_interval_ms});
    </script>
    """.format(refresh_interval_ms=refresh_interval_ms)
    return css + html_body + javascript

async def check_backend_ready(url: str, timeout: int = 2) -> bool:
    """非同步檢查後端服務是否已就緒。"""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            # 我們預期主儀表板的根目錄或 /health 能回傳 200 OK
            response = await client.get(url)
            return response.status_code == 200
    except (httpx.ConnectError, httpx.TimeoutException):
        return False

async def serve_proxy_url_with_retry(health_check_url: str, port: int, retries: int, delay: int):
    """
    帶重試邏輯，檢查後端並顯示 Colab 代理 URL。
    這應在一個獨立的執行緒中執行，以避免阻塞主執行緒。
    """
    import asyncio
    update_status(log=f"🔗 [URL 服務] 已啟動，開始監控後端健康狀態...")
    for attempt in range(retries):
        if await check_backend_ready(health_check_url):
            update_status(log=f"✅ [URL 服務] 後端服務已就緒，正在生成代理 URL...")
            try:
                # 根據 Colab 的建議，改用更穩定的 iframe 方法
                colab_output.serve_kernel_port_as_iframe(port, height=800)
                update_status(log="✅ [URL 服務] Colab 代理 iframe 已成功顯示。")
            except Exception as e:
                update_status(log=f"❌ [URL 服務] 呼叫 serve_kernel_port_as_iframe 失敗: {e}")
            return # 任務完成，無論成功或失敗

        if attempt < retries - 1:
            update_status(log=f"🟡 [URL 服務] 後端尚未就緒 (嘗試 {attempt + 1}/{retries})，將在 {delay} 秒後重試...")
            await asyncio.sleep(delay)

    update_status(log=f"❌ [URL 服務] 在 {retries} 次嘗試後，後端服務仍未回應。URL 無法生成。")


def main():
    update_status(log="指揮中心 V19 (API驅動版) 啟動。")

    clear_output(wait=True)
    display(HTML(render_dashboard_html()))

    worker_thread = threading.Thread(target=background_worker)
    worker_thread.start()

    # 啟動 URL 服務執行緒
    # 這個執行緒會等待後端服務就緒，然後嘗試顯示 Colab URL
    import asyncio
    url_service_thread = threading.Thread(
        target=lambda: asyncio.run(serve_proxy_url_with_retry(
            health_check_url="http://localhost:8000/health", # 使用我們新增的、更可靠的健康檢查端點
            port=8000,
            retries=COLAB_URL_RETRIES,
            delay=COLAB_URL_RETRY_DELAY
        )),
        daemon=True
    )
    url_service_thread.start()

    # 採用更健壯的邏輯：前端等待後端程序結束，並在被中斷時觸發後端優雅關閉。
    try:
        # 等待後端程序 handle 被建立
        launch_process_local = None
        while not launch_process_local:
            with status_lock:
                launch_process_local = shared_status.get("launch_process")
            if not worker_thread.is_alive() and not launch_process_local:
                 raise RuntimeError("背景工作執行緒結束，但未能啟動後端服務。")
            time.sleep(0.5)

        update_status(log="[前端] 後端已啟動，前端進入待命模式。請使用儀表板上的關閉按鈕，或手動中斷此儲存格來結束任務。")

        # 等待後端程序結束。這比無限睡眠更健壯。
        # launch_process_local 是 Popen 物件
        if launch_process_local:
            exit_code = launch_process_local.wait()
            update_status(log=f"[前端] 後端程序已結束，返回碼: {exit_code}。前端任務完成。")

    except (KeyboardInterrupt, Exception) as e:
        print("\n" + "="*80)
        print("🛑 前端儲存格被手動中斷或發生錯誤，正在嘗試優雅關閉後端服務...")
        print("="*80)
        try:
            # 檢查後端程序是否仍在運行
            with status_lock:
                launch_process_local = shared_status.get("launch_process")

            if launch_process_local and launch_process_local.poll() is None:
                shutdown_url = 'http://localhost:8088/api/v1/shutdown'
                print(f"正在向 {shutdown_url} 發送關閉信號...")
                # 使用 httpx 的同步 client
                with httpx.Client() as client:
                    response = client.post(shutdown_url, timeout=10)

                if response.status_code == 200:
                    print("✅ 成功發送關閉信號。後端將在背景完成報告生成與歸檔。")
                    print("   請等待約 30 秒後，在 Colab 左側檔案總管的歸檔資料夾中檢查報告。")
                else:
                    print(f"⚠️ 發送關閉信號失敗，後端回應: {response.status_code}。嘗試強制終止...")
                    launch_process_local.terminate()
            else:
                print("ℹ️ 後端程序似乎已經結束，無需發送關閉信號。")

        except Exception as shutdown_exc:
            print(f"❌ 在嘗試優雅關閉後端時發生錯誤: {shutdown_exc}")
            print("   報告可能無法正常生成。")

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
