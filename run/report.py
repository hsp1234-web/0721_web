# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║                  📊 報告中心 V24 (非同步儀表板)                    ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   - 架構：採用與主指揮中心相同的非同步儀表板架構。                 ║
# ║   - 體驗：立即顯示介面，背景處理依賴與環境，按需生成報告。         ║
# ║   - 隔離：為報告生成器建立獨立的 Venv，不污染主環境。              ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 📊 報告中心 v24 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **報告目標設定**
#@markdown > **指定包含 `state.db` 的專案資料夾。**
#@markdown ---
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
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

try:
    from IPython.display import display, HTML, clear_output
    import nest_asyncio
    from aiohttp import web
except ImportError:
    print("正在安裝報告中心核心依賴 (ipython, nest_asyncio, aiohttp)...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "ipython", "nest_asyncio", "aiohttp"])
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

# --- 後端邏輯 ---

def update_state(status=None, log=None, report_name=None, report_content=None, error=None):
    with state_lock:
        if status:
            shared_state["status"] = status
        if log:
            shared_state["logs"].append(f"[{time.strftime('%H:%M:%S')}] {log}")
        if report_name and report_content:
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

        if not app_path.exists() or not req_file.exists():
            raise FileNotFoundError(f"找不到報告生成器應用或其需求檔案: {app_path}")

        # 1. 建立 Venv
        if not venv_path.exists():
            update_state(log=f"未找到 Venv，正在建立於 {venv_path}...")
            uv_cmd = ["uv", "venv", str(venv_path)]
            proc = subprocess.run(uv_cmd, capture_output=True, text=True, cwd=project_path)
            if proc.returncode != 0:
                raise RuntimeError(f"建立 Venv 失敗: {proc.stderr}")
            update_state(log="✅ Venv 建立成功。")

        # 2. 安裝依賴
        update_state(status="安裝依賴中", log="正在使用 uv 安裝報告依賴...")
        python_executable = str(venv_path / "bin" / "python")
        uv_install_cmd = ["uv", "pip", "install", "-r", str(req_file), "--python", python_executable]
        proc = subprocess.run(uv_install_cmd, capture_output=True, text=True, cwd=project_path)
        if proc.returncode != 0:
            raise RuntimeError(f"安裝依賴失敗: {proc.stderr}")
        update_state(log="✅ 依賴安裝成功。")

        update_state(status="準備就緒", log="報告中心已準備就緒，請點擊按鈕生成報告。")

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        update_state(status="環境準備失敗", log=f"❌ {e}", error=error_details)
    finally:
        with state_lock:
            shared_state["background_task_done"] = True

# --- API 伺服器 ---
async def get_status(request):
    with state_lock:
        return web.json_response({
            "status": shared_state["status"],
            "logs": list(shared_state["logs"]),
            "error": shared_state["error"],
        })

async def generate_report(request):
    """處理報告生成請求"""
    if shared_state['status'] != "準備就緒":
         return web.json_response({"error": "報告生成器尚未準備就緒。"}, status=400)

    try:
        data = await request.json()
        report_type = data.get("type")
        if not report_type:
            raise ValueError("請求中未指定報告類型。")

        update_state(status=f"正在生成 {report_type} 報告...", log=f"收到請求，開始生成 {report_type} 報告。")

        project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")
        venv_python = str(project_path / "apps" / "report_generator" / ".venv" / "bin" / "python")

        # 執行 generate_report.py 腳本
        report_script_path = project_path / "scripts" / "generate_report.py"
        db_file = project_path / "state.db"
        config_file = project_path / "config.json"

        cmd = [
            venv_python, str(report_script_path),
            "--db-file", str(db_file),
            "--config-file", str(config_file)
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True, cwd=project_path)

        if proc.returncode != 0:
            raise RuntimeError(f"報告生成腳本執行失敗: {proc.stderr}")

        update_state(log="✅ 核心報告腳本執行成功。")

        # 讀取所有報告檔案
        logs_dir = project_path / "logs"
        report_files = {
            "summary": "summary_report.md",
            "performance": "performance_report.md",
            "log": "detailed_log_report.md",
        }

        reports_content = {}
        for key, filename in report_files.items():
            path = logs_dir / filename
            if path.exists():
                reports_content[key] = path.read_text(encoding="utf-8")

        update_state(status="準備就緒", log="所有報告均已生成/更新。")
        return web.json_response({"reports": reports_content})

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        update_state(status="報告生成失敗", log=f"❌ {e}", error=error_details)
        return web.json_response({"error": str(e), "details": error_details}, status=500)


async def api_server():
    app = web.Application()
    app.router.add_get("/api/status", get_status)
    app.router.add_post("/api/generate", generate_report)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, 'localhost', 8089) # 使用一個新的埠
    await site.start()
    with state_lock:
        shared_state["api_server_running"] = True
    update_state(log="內部 API 伺服器已在 http://localhost:8089 啟動")
    await asyncio.Event().wait() # 永遠等待

# --- 前端顯示 ---
def render_html():
    css = """
    <style>
        body { background-color: #1a2a3a; color: #e0e0e0; font-family: 'Noto Sans TC', monospace; }
        .container { padding: 1em; }
        .panel { border: 1px solid #4a6a8a; margin-bottom: 1em; background-color: #2a3a4a; }
        .title { font-weight: bold; padding: 0.5em; border-bottom: 1px solid #4a6a8a; background-color: #3a5a7a;}
        .log-panel { height: 200px; overflow-y: auto; padding: 0.5em; font-size: 0.9em; }
        .report-panel { min-height: 300px; padding: 1em; white-space: pre-wrap; word-break: break-all; }
        .button-bar { padding: 0.5em; text-align: center; }
        .report-btn { background-color: #3498db; color: white; border: none; padding: 8px 15px; margin: 0 5px; cursor: pointer; border-radius: 5px; }
        .report-btn:disabled { background-color: #555; cursor: not-allowed; }
        .copy-btn { background-color: #2ecc71; float: right; }
        .status-bar { padding: 0.5em; text-align: center; border-top: 1px solid #4a6a8a; font-size: 0.9em;}
    </style>
    """
    html = """
    <div class="container">
        <div class="panel">
            <div class="title">📊 報告中心狀態</div>
            <div class="log-panel" id="log-container"></div>
        </div>
        <div class="panel">
            <div class="title">📋 報告內容</div>
            <div class="button-bar" id="button-bar">
                <button class="report-btn" id="btn-summary" onclick="fetchReport('summary')" disabled>總結報告</button>
                <button class="report-btn" id="btn-performance" onclick="fetchReport('performance')" disabled>效能報告</button>
                <button class="report-btn" id="btn-log" onclick="fetchReport('log')" disabled>詳細日誌</button>
            </div>
            <div class="report-panel" id="report-content">
                <button class="report-btn copy-btn" id="copy-report-btn" style="display:none;" onclick="copyReport()">複製報告</button>
                <div id="report-display">請點擊上方按鈕以生成並載入報告。</div>
            </div>
        </div>
        <div class="status-bar" id="status-bar">初始化中...</div>
    </div>
    """
    js = """
    <script>
        let currentReportContent = "";
        let allReports = {};

        function setButtonsDisabled(disabled) {
            document.getElementById('btn-summary').disabled = disabled;
            document.getElementById('btn-performance').disabled = disabled;
            document.getElementById('btn-log').disabled = disabled;
        }

        async function updateStatus() {
            try {
                const response = await fetch('/api/status');
                const data = await response.json();

                document.getElementById('status-bar').textContent = `狀態: ${data.status}`;

                const logContainer = document.getElementById('log-container');
                logContainer.innerHTML = data.logs.join('\\n');
                logContainer.scrollTop = logContainer.scrollHeight;

                if (data.status === '準備就緒') {
                    setButtonsDisabled(false);
                } else {
                    setButtonsDisabled(true);
                }
            } catch (e) {
                document.getElementById('status-bar').textContent = '錯誤：無法連接到後端狀態 API。';
            }
        }

        async function fetchReport(reportType) {
            setButtonsDisabled(true);
            document.getElementById('status-bar').textContent = `狀態: 正在請求 ${reportType} 報告...`;
            document.getElementById('report-display').textContent = '報告生成中，請稍候...';

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ type: reportType })
                });
                const data = await response.json();
                if (data.error) throw new Error(data.error);

                allReports = data.reports;
                displayReport(reportType);

            } catch (e) {
                document.getElementById('report-display').textContent = `錯誤: ${e.message}`;
            } finally {
                setButtonsDisabled(false);
            }
        }

        function displayReport(reportType) {
            const content = allReports[reportType];
            if (content) {
                document.getElementById('report-display').textContent = content;
                currentReportContent = content;
                document.getElementById('copy-report-btn').style.display = 'block';
            } else {
                document.getElementById('report-display').textContent = `未找到 '${reportType}' 報告的內容。請先生成。`;
                document.getElementById('copy-report-btn').style.display = 'none';
            }
        }

        function copyReport() {
            const btn = document.getElementById('copy-report-btn');
            navigator.clipboard.writeText(currentReportContent).then(() => {
                btn.textContent = '已複製!';
                setTimeout(() => { btn.textContent = '複製報告'; }, 2000);
            }, () => {
                alert('複製失敗！');
            });
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

    # 在背景執行緒中啟動後端任務
    worker = threading.Thread(target=background_worker, daemon=True)
    worker.start()

    # 在主執行緒中啟動 API 伺服器 (因為 nest_asyncio)
    try:
        asyncio.run(api_server())
    except KeyboardInterrupt:
        print("\n報告中心已被手動中斷。")
    except Exception as e:
        update_state(log=f"❌ API 伺服器發生致命錯誤: {e}", error=str(e))


if __name__ == "__main__":
    main()
