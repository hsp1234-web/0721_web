# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║               📊 報告中心 V25 (互動式儀表板)                       ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   - 架構：採非同步儀表板架構，提供流暢的即時體驗。                 ║
# ║   - 功能：按需預覽報告、一鍵歸檔所有報告、複製儀表板狀態。         ║
# ║   - 隔離：為報告生成器建立獨立 Venv，不污染主環境。                ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 📊 報告中心 v25 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 基礎設定**
#@markdown > **指定包含 `state.db` 的專案資料夾，以及報告的歸檔位置。**
#@markdown ---
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **報告歸檔資料夾 (REPORT_ARCHIVE_FOLDER)**
#@markdown > **報告將歸檔至 `/content/<專案資料夾>/<此處指定的名稱>`**
REPORT_ARCHIVE_FOLDER = "作戰日誌歸檔" #@param {type:"string"}
#@markdown ---
#@markdown > **點擊「執行」以啟動報告中心儀表板。**
#@markdown ---

import os
import sys
import shutil
import subprocess
from pathlib import Path
import time
import json
import threading
import asyncio
from collections import deque
import pytz

try:
    from IPython.display import display, HTML, clear_output
    import nest_asyncio
    from aiohttp import web
except ImportError:
    print("正在安裝報告中心核心依賴 (ipython, nest_asyncio, aiohttp)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ipython", "nest_asyncio", "aiphttp"])
    from IPython.display import display, HTML, clear_output
    import nest_asyncio
    from aiohttp import web

nest_asyncio.apply()

# --- 全域共享狀態 ---
shared_state = {
    "status": "初始化中...",
    "logs": deque(maxlen=50),
    "reports": {},
    "api_server_running": False,
    "background_task_done": False,
    "error": None,
}
state_lock = threading.Lock()
# --- 全域 API 伺服器實例 ---
api_app_runner = None

# --- 後端邏輯 ---

def update_state(status=None, log=None, report_name=None, report_content=None, error=None):
    with state_lock:
        if status:
            shared_state["status"] = status
        if log:
            shared_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {log}")
        if report_name and report_content is not None:
            shared_state["reports"][report_name] = report_content
        if error:
            shared_state["error"] = error
            shared_state["status"] = "發生錯誤"

def background_worker():
    """在背景準備報告生成環境 (Venv, Dependencies)"""
    try:
        project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")
        app_path = project_path / "apps" / "report_generator"
        venv_path = app_path / ".venv"
        req_file = app_path / "requirements.txt"

        update_state(status="環境準備中", log="正在檢查報告生成器環境...")

        if not app_path.is_dir() or not req_file.is_file():
            raise FileNotFoundError(f"找不到報告生成器應用或其需求檔案: {app_path}")

        if not venv_path.exists():
            update_state(log=f"未找到 Venv，正在建立於 {venv_path}...")
            uv_cmd = ["uv", "venv", str(venv_path), "--python", sys.executable]
            proc = subprocess.run(uv_cmd, capture_output=True, text=True, cwd=project_path, check=True)
            update_state(log="✅ Venv 建立成功。")

        update_state(status="安裝依賴中", log="正在使用 uv 安裝報告依賴...")
        python_executable = str(venv_path / "bin" / "python")
        uv_install_cmd = ["uv", "pip", "install", "-r", str(req_file), "--python", python_executable]
        proc = subprocess.run(uv_install_cmd, capture_output=True, text=True, cwd=project_path, check=True)
        update_state(log="✅ 依賴安裝成功。")

        update_state(status="準備就緒", log="報告中心已準備就緒，請點擊按鈕操作。")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        update_state(status="環境準備失敗", log=f"❌ {e}", error=error_details)
    finally:
        with state_lock:
            shared_state["background_task_done"] = True

def run_report_generation(project_path):
    """執行核心的 generate_report.py 腳本"""
    venv_python = str(project_path / "apps" / "report_generator" / ".venv" / "bin" / "python")
    report_script_path = project_path / "scripts" / "generate_report.py"
    db_file = project_path / "state.db"
    config_file = project_path / "config.json"

    if not db_file.exists() or not config_file.exists():
        raise FileNotFoundError("找不到 state.db 或 config.json，無法生成報告。")

    cmd = [
        venv_python, str(report_script_path),
        "--db-file", str(db_file), "--config-file", str(config_file)
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path, check=True)
    update_state(log="✅ 核心報告腳本執行成功。")
    return True

# --- API 伺服器 ---
async def get_status(request):
    with state_lock:
        return web.json_response({
            "status": shared_state["status"],
            "logs": list(shared_state["logs"]),
            "error": shared_state["error"],
        })

async def generate_and_get_report(request):
    if shared_state['status'] != "準備就緒":
        return web.json_response({"error": "報告生成器尚未準備就緒。"}, status=400)
    try:
        data = await request.json()
        report_type = data.get("type")
        update_state(status=f"正在生成報告...", log=f"收到請求，開始生成所有報告。")

        project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")
        run_report_generation(project_path)

        logs_dir = project_path / "logs"
        report_files = {
            "summary": "summary_report.md", "performance": "performance_report.md", "log": "detailed_log_report.md"
        }

        reports_content = {}
        for key, filename in report_files.items():
            path = logs_dir / filename
            reports_content[key] = path.read_text(encoding="utf-8") if path.exists() else f"# 未找到報告: {filename}"

        update_state(status="準備就緒", log="報告預覽已更新。")
        return web.json_response({"reports": reports_content})
    except Exception as e:
        update_state(status="報告生成失敗", log=f"❌ {e}", error=traceback.format_exc())
        return web.json_response({"error": str(e)}, status=500)

async def archive_reports(request):
    if shared_state['status'] != "準備就緒":
        return web.json_response({"error": "報告生成器尚未準備就緒。"}, status=400)
    try:
        update_state(status="歸檔中...", log="收到歸檔請求...")
        project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")

        # 1. 確保報告是最新
        run_report_generation(project_path)

        # 2. 執行歸檔
        archive_base_path = project_path / REPORT_ARCHIVE_FOLDER
        archive_base_path.mkdir(exist_ok=True)

        tz = pytz.timezone("Asia/Taipei")
        timestamp_folder_name = datetime.now(tz).isoformat(timespec='seconds')
        archive_target_path = archive_base_path / timestamp_folder_name
        archive_target_path.mkdir()

        update_state(log=f"建立歸檔資料夾: {archive_target_path}")

        rename_map = {
            "summary_report.md": "任務總結報告.md",
            "performance_report.md": "效能分析報告.md",
            "detailed_log_report.md": "詳細日誌報告.md"
        }

        logs_dir = project_path / "logs"
        for old_name, new_name in rename_map.items():
            source_path = logs_dir / old_name
            if source_path.exists():
                shutil.move(str(source_path), str(archive_target_path / new_name))
                update_state(log=f"  - 已歸檔: {new_name}")

        final_log = f"✅ 所有報告已成功歸檔至: {archive_target_path}"
        update_state(status="準備就緒", log=final_log)
        return web.json_response({"message": final_log, "path": str(archive_target_path)})

    except Exception as e:
        update_state(status="歸檔失敗", log=f"❌ {e}", error=traceback.format_exc())
        return web.json_response({"error": str(e)}, status=500)

async def start_api_server():
    global api_app_runner
    app = web.Application()
    app.router.add_get("/api/status", get_status)
    app.router.add_post("/api/generate", generate_and_get_report)
    app.router.add_post("/api/archive", archive_reports)

    api_app_runner = web.AppRunner(app)
    await api_app_runner.setup()
    site = web.TCPSite(api_app_runner, 'localhost', 8089)
    await site.start()

    with state_lock:
        shared_state["api_server_running"] = True
    update_state(log="內部 API 伺服器已在 http://localhost:8089 啟動")

# --- 前端顯示 ---
def render_html():
    # ... (HTML and JS content from V-Final.3, with updated button bar and API calls)
    css = """
    <style>
        body { background-color: #1a2a3a; color: #e0e0e0; font-family: 'Noto Sans TC', monospace; }
        .container { padding: 1em; }
        .panel { border: 1px solid #4a6a8a; margin-bottom: 1em; background-color: #2a3a4a; }
        .title { font-weight: bold; padding: 0.5em; border-bottom: 1px solid #4a6a8a; background-color: #3a5a7a;}
        .log-panel { height: 150px; overflow-y: auto; padding: 0.5em; font-size: 0.85em; border: 1px solid #4a6a8a; margin: 0.5em;}
        .report-panel { min-height: 250px; padding: 1em; white-space: pre-wrap; word-break: break-all; position: relative;}
        .button-bar { padding: 0.5em; text-align: center; border-bottom: 1px solid #4a6a8a; }
        .action-bar { padding: 0.8em; text-align: center; }
        .report-btn, .action-btn { font-size: 1em; border: none; padding: 8px 15px; margin: 0 5px; cursor: pointer; border-radius: 5px; }
        .report-btn { background-color: #3498db; color: white; }
        .action-btn.archive { background-color: #9b59b6; color: white; }
        .action-btn.copy-state { background-color: #2ecc71; color: white; }
        .report-btn:disabled, .action-btn:disabled { background-color: #555; cursor: not-allowed; }
        .copy-report-btn { background-color: #f1c40f; color: #111; position: absolute; top: 10px; right: 10px; }
        .status-bar { padding: 0.5em; text-align: center; border-top: 1px solid #4a6a8a; font-size: 0.9em;}
    </style>
    """
    html = """
    <div class="container">
        <div class="panel">
            <div class="title">📊 報告中心</div>
            <div class="log-panel" id="log-container"></div>
            <div class="status-bar" id="status-bar">初始化中...</div>
        </div>
        <div class="panel">
            <div class="title">📋 報告預覽</div>
            <div class="button-bar" id="preview-button-bar">
                <button class="report-btn" id="btn-summary" onclick="displayReport('summary')" disabled>總結報告</button>
                <button class="report-btn" id="btn-performance" onclick="displayReport('performance')" disabled>效能報告</button>
                <button class="report-btn" id="btn-log" onclick="displayReport('log')" disabled>詳細日誌</button>
            </div>
            <div class="report-panel" id="report-content">
                <button class="report-btn copy-report-btn" id="copy-report-btn" style="display:none;" onclick="copyCurrentReport()">複製此報告</button>
                <div id="report-display">請在上方按鈕啟用後，點擊以載入報告預覽。</div>
            </div>
        </div>
        <div class="panel">
            <div class="title">⚙️ 主要操作</div>
            <div class="action-bar">
                <button class="action-btn archive" id="btn-archive" onclick="archiveAllReports()" disabled>📁 歸檔所有報告</button>
                <button class="action-btn copy-state" id="btn-copy-state" onclick="copyDashboardState()">📋 複製儀表板狀態</button>
            </div>
        </div>
    </div>
    """
    js = """
    <script>
        let currentDashboardState = {};
        let allReports = {};

        function setAllButtonsDisabled(disabled) {
            document.querySelectorAll('.report-btn, .action-btn.archive').forEach(btn => btn.disabled = disabled);
        }

        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                currentDashboardState = await response.json();

                document.getElementById('status-bar').textContent = `狀態: ${currentDashboardState.status}`;
                const logContainer = document.getElementById('log-container');
                logContainer.innerHTML = currentDashboardState.logs.join('\\n');
                logContainer.scrollTop = logContainer.scrollHeight;

                if (currentDashboardState.status === '準備就緒') {
                    setAllButtonsDisabled(false);
                } else {
                    setAllButtonsDisabled(true);
                }
            } catch (e) {
                document.getElementById('status-bar').textContent = '錯誤：無法連接到後端狀態 API。';
            }
        }

        async function generateAndLoadReports() {
             setAllButtonsDisabled(true);
             updateStateText('正在生成所有報告...');
             try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ type: 'all' }) // API now generates all at once
                });
                const data = await response.json();
                if (data.error) throw new Error(data.error);
                allReports = data.reports;
                updateStateText('報告已更新，請選擇預覽。');
             } catch (e) {
                updateStateText(`錯誤: ${e.message}`);
             } finally {
                setAllButtonsDisabled(false);
             }
        }

        function displayReport(reportType) {
            if (!allReports[reportType]) {
                generateAndLoadReports().then(() => {
                    const content = allReports[reportType] || `未找到 '${reportType}' 報告。`;
                    document.getElementById('report-display').textContent = content;
                    document.getElementById('copy-report-btn').style.display = 'block';
                });
            } else {
                const content = allReports[reportType];
                document.getElementById('report-display').textContent = content;
                document.getElementById('copy-report-btn').style.display = 'block';
            }
        }

        async function archiveAllReports() {
            setAllButtonsDisabled(true);
            updateStateText('正在歸檔所有報告...');
            try {
                const response = await fetch('/api/archive', { method: 'POST' });
                const data = await response.json();
                if (data.error) throw new Error(data.error);
                updateStateText(data.message);
            } catch (e) {
                updateStateText(`歸檔失敗: ${e.message}`);
            } finally {
                 setAllButtonsDisabled(false);
            }
        }

        function copyToClipboard(text, buttonId, originalText) {
            const btn = document.getElementById(buttonId);
            navigator.clipboard.writeText(text).then(() => {
                btn.textContent = '已複製!';
                setTimeout(() => { btn.textContent = originalText; }, 2000);
            }, () => { alert('複製失敗！'); });
        }

        function copyCurrentReport() {
            const reportContent = document.getElementById('report-display').textContent;
            copyToClipboard(reportContent, 'copy-report-btn', '複製此報告');
        }

        function copyDashboardState() {
            let text = '📊 報告中心狀態報告 (即時)\\n';
            text += '========================\\n';
            text += `狀態: ${currentDashboardState.status}\\n\\n`;
            text += '日誌:\\n';
            text += currentDashboardState.logs.join('\\n');
            copyToClipboard(text, 'btn-copy-state', '📋 複製儀表板狀態');
        }

        function updateStateText(text) {
             document.getElementById('status-bar').textContent = `狀態: ${text}`;
        }

        setInterval(updateStatus, 2000);
        updateStatus();
    </script>
    """
    return f"<html><head>{css}</head><body>{html}{js}</body></html>"

# --- 主執行函數 ---
def main():
    clear_output(wait=True)
    display(HTML(render_html()))

    loop = asyncio.get_event_loop()
    if loop.is_running():
        print("Asyncio loop is already running. Using existing loop.")
    else:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    # 啟動背景準備任務
    worker = threading.Thread(target=background_worker, daemon=True)
    worker.start()

    # 啟動 API 伺服器
    api_thread = threading.Thread(target=lambda: asyncio.run(start_api_server()), daemon=True)
    api_thread.start()

    # 主執行緒等待背景任務完成，或直到被中斷
    try:
        while not shared_state["background_task_done"]:
            time.sleep(1)
            # 在此期間，API 伺服器和背景任務都在運行
            if shared_state["error"]:
                print(f"背景任務發生錯誤: {shared_state['error']}")
                break

        if not shared_state["error"]:
             print("報告中心已準備就緒。此儲存格將保持運行以提供後端服務。您可以隨時手動中斷它。")

        # 保持主執行緒存活以接收中斷信號
        while True:
            time.sleep(3600)

    except KeyboardInterrupt:
        print("\n報告中心已被使用者手動中斷。")
    finally:
        # 嘗試優雅關閉 aiohttp
        if api_app_runner:
            loop.run_until_complete(api_app_runner.cleanup())
        print("報告中心已關閉。")

if __name__ == "__main__":
    main()
