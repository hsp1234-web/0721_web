# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║      🚀 Colab HTML 動態儀表板 v14.0                                ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   採用動態生成 HTML+CSS 的方式，提供像素級精準的儀表板。           ║
# ║   後端作為守護進程持續運行，前端顯示迴圈永不中斷。                 ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心 HTML 啟動器 v14.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "4.2.5" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}
#@markdown ---
#@markdown ### **Part 2: 模式設定**
#@markdown > **用於快速驗證或完整部署。**
#@markdown ---
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

def render_dashboard_html(status_row, log_rows):
    """根據資料庫狀態生成儀表板的 HTML"""
    stage, apps_status_json, action_url, cpu, ram = status_row
    apps_status = json.loads(apps_status_json) if apps_status_json else {}

    # CSS 樣式
    css = """
    <style>
        .dashboard-container { background-color: transparent; font-family: 'Fira Code', 'Noto Sans TC', monospace; color: #FFFFFF; padding: 1em; }
        .panel { border: 1px solid #FFFFFF; margin-bottom: 1em; }
        .panel-title { font-weight: bold; padding: 0.5em; border-bottom: 1px solid #FFFFFF; }
        .panel-content { padding: 0.5em; }
        .flex-container { display: flex; gap: 1em; }
        .left-column { flex: 1; }
        .right-column { flex: 2; }
        .log-entry { margin-bottom: 0.5em; }
        .log-level-WARNING { color: #fbbc04; }
        .log-level-ERROR, .log-level-CRITICAL { color: #ea4335; }
        .footer { text-align: center; padding-top: 1em; border-top: 1px solid #FFFFFF; }
        a { color: #34a853; font-weight: bold; }
        table { width: 100%; }
    </style>
    """

    # --- HTML 生成邏輯 ---
    def get_app_status_rows():
        rows = ""
        status_map = {
            "running": "<span>🟢</span> Running",
            "pending": "<span>🟡</span> Pending",
            "starting": "<span>🟡</span> Starting",
            "failed": "<span>🔴</span> Failed"
        }
        for app, status in apps_status.items():
            display_status = status_map.get(status, f"<span>❓</span> {status}")
            rows += f"<tr><td>{app.capitalize()}</td><td>{display_status}</td></tr>"
        return rows

    def get_log_entries():
        entries = ""
        for ts, level, msg in reversed(log_rows):
            ts_str = str(ts).split(" ")[1][:8] if ts else "--------"
            level_class = f"log-level-{level}" if level in ["WARNING", "ERROR", "CRITICAL"] else ""
            entries += f'<div class="log-entry"><span class="{level_class}">{ts_str} [{level.ljust(8)}] {msg}</span></div>'
        return entries

    def get_footer_content():
        if action_url:
            return f'✅ 啟動完成！操作儀表板連結: <a href="{action_url}" target="_blank">{action_url}</a>'
        if stage in ["failed", "critical_failure"]:
            return '<span class="log-level-ERROR">❌ 啟動失敗。請檢查日誌。</span>'
        return f"⏳ 當前階段: {stage.upper()}"

    html = f"""
    <div class="dashboard-container">
        <div class="flex-container">
            <div class="left-column">
                <div class="panel">
                    <div class="panel-title">微服務狀態</div>
                    <div class="panel-content">
                        <table>{get_app_status_rows()}</table>
                    </div>
                </div>
                <div class="panel">
                    <div class="panel-title">系統資源</div>
                    <div class="panel-content">
                        <table>
                            <tr><td>CPU</td><td>{cpu or 0.0:.1f}%</td></tr>
                            <tr><td>RAM</td><td>{ram or 0.0:.1f}%</td></tr>
                        </table>
                    </div>
                </div>
            </div>
            <div class="right-column">
                <div class="panel">
                    <div class="panel-title">即時日誌</div>
                    <div class="panel-content">{get_log_entries()}</div>
                </div>
            </div>
        </div>
        <div class="footer">{get_footer_content()}</div>
    </div>
    """
    return css + html

base_path = Path("/content")

def main():
    # --- 全域路徑與變數 ---
    project_path = base_path / PROJECT_FOLDER_NAME
    db_file = project_path / "state.db"

    # --- 步驟 1: 準備專案 ---
    print("🚀 鳳凰之心 HTML 啟動器 v14.0")
    print("="*80)
    print("1. 準備專案目錄...")
    if FORCE_REPO_REFRESH and project_path.exists():
        shutil.rmtree(project_path)
    if not project_path.exists():
        git_command = ["git", "clone", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", "-q", REPOSITORY_URL, str(project_path)]
        subprocess.run(git_command, check=True, cwd=base_path)
    os.chdir(project_path)
    print(f"✅ 專案準備完成於: {os.getcwd()}")

    # --- 步驟 2: 安裝核心依賴 ---
    print("\n2. 安裝核心 Python 依賴...")
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    all_reqs_path = project_path / "all_requirements.txt"
    with open(all_reqs_path, "w") as outfile:
        for app_dir in (project_path / "apps").iterdir():
            if app_dir.is_dir():
                req_file = app_dir / "requirements.txt"
                if req_file.exists():
                    with open(req_file) as infile:
                        outfile.write(infile.read())
                    outfile.write("\n")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(all_reqs_path)], check=True)
    print("✅ 所有依賴安裝完成。")

    # --- 步驟 3: 在背景啟動後端主力部隊 ---
    print("\n3. 觸發背景服務啟動程序...")
    env = os.environ.copy()
    env["DB_FILE"] = str(db_file)
    if FAST_TEST_MODE:
        env["FAST_TEST_MODE"] = "true"
        print("   - 🚀 快速測試模式已啟用。")

    log_file = project_path / "logs" / "launch.log"
    log_file.parent.mkdir(exist_ok=True)

    with open(log_file, "w") as f:
        launch_process = subprocess.Popen(
            [sys.executable, "launch.py"],
            env=env, stdout=f, stderr=subprocess.STDOUT
        )
    print(f"✅ 後端主力部隊 (launch.py) 已在背景啟動 (PID: {launch_process.pid})。")
    print(f"   - 日誌將寫入: {log_file}")

    # --- 步驟 4: 啟動前端戰情顯示器 ---
    print("\n4. 正在啟動前端戰情顯示器...")
    time.sleep(2)

    try:
        while True:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT current_stage, apps_status, action_url, cpu_usage, ram_usage FROM status_table WHERE id = 1")
                status_row = cursor.fetchone()
                cursor.execute("SELECT timestamp, level, message FROM log_table ORDER BY id DESC LIMIT 10")
                log_rows = cursor.fetchall()
                conn.close()

                if not status_row:
                    time.sleep(1)
                    continue
            except sqlite3.OperationalError as e:
                if "no such table" in str(e):
                    time.sleep(1)
                    continue
                raise

            clear_output(wait=True)
            display(HTML(render_dashboard_html(status_row, log_rows)))
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 偵測到手動中斷！正在終止後端服務...")
        launch_process.terminate()
        print("✅ 後端服務已被終止。")
    except Exception as e:
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
