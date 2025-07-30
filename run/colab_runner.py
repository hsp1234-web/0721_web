# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║      🚀 Colab HTML 動態儀表板 V15                                  ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   採用動態生成 HTML+CSS 的方式，提供像素級精準的儀表板。           ║
# ║   後端作為守護進程持續運行，前端顯示迴圈永不中斷。                 ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心指揮中心 V15 (最終穩定版) { vertical-output: true, display-mode: "form" }
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

def archive_reports(project_path, archive_folder_name, timezone_str):
    """將生成的報告歸檔到指定目錄"""
    if not archive_folder_name:
        print("ℹ️ 日誌歸檔功能已關閉。")
        return

    try:
        archive_base_path = Path("/content") / archive_folder_name
        archive_base_path.mkdir(exist_ok=True)

        tz = pytz.timezone(timezone_str)
        timestamp_folder_name = datetime.now(tz).isoformat()
        archive_target_path = archive_base_path / timestamp_folder_name
        archive_target_path.mkdir()

        source_reports_path = project_path / "logs"
        report_files = [
            "綜合戰情簡報.md",
            "效能分析報告.md",
            "詳細日誌報告.md"
        ]

        print(f"🗄️ 開始歸檔報告至: {archive_target_path}")
        for report_name in report_files:
            source_file = source_reports_path / report_name
            if source_file.exists():
                shutil.move(str(source_file), str(archive_target_path / report_name))
                print(f"  - 已移動: {report_name}")
            else:
                print(f"  - 警告: 找不到報告檔案 {report_name}")

        print("✅ 報告歸檔完成。")

    except Exception as e:
        print(f"❌ 歸檔報告時發生錯誤: {e}")


def render_dashboard_html(status_row, log_rows, config):
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
    print("🚀 鳳凰之心指揮中心 V15")
    print("="*80)
    print("1. 準備專案環境...")

    if FORCE_REPO_REFRESH and project_path.exists():
        print(f"  - 偵測到強制刷新，正在刪除舊的專案資料夾: {project_path}")
        shutil.rmtree(project_path)

    if not project_path.exists():
        print(f"  - 正在從 {REPOSITORY_URL} 的分支 {TARGET_BRANCH_OR_TAG} 下載程式碼...")
        try:
            subprocess.run(
                ["git", "clone", "--depth", "1", "--branch", TARGET_BRANCH_OR_TAG, REPOSITORY_URL, str(project_path)],
                check=True, capture_output=True, text=True
            )
            print("  - ✅ 程式碼下載成功。")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git clone 失敗: {e.stderr}")
            return # 終止執行
    else:
        print("  - 專案資料夾已存在，跳過下載。")

    # --- 步驟 2: 生成設定檔 ---
    print("\n2. 生成專案設定檔...")
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
    print(f"✅ 設定檔已生成於: {config_file}")

    # --- 步驟 3: 安裝核心依賴 ---
    # ... (安裝邏輯保持不變)

    # --- 步驟 3: 在背景啟動後端主力部隊 ---
    print("\n3. 觸發背景服務啟動程序...")

    # 確保日誌目錄存在
    logs_dir = project_path / "logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    env = os.environ.copy()
    env["DB_FILE"] = str(db_file)
    if FAST_TEST_MODE:
        env["FAST_TEST_MODE"] = "true"

    log_file = logs_dir / "launch.log"
    with open(log_file, "w") as f:
        launch_process = subprocess.Popen(
            [sys.executable, str(project_path / "launch.py")],
            cwd=project_path,
            env=env,
            stdout=f,
            stderr=subprocess.STDOUT
        )
    print(f"✅ 後端主力部隊 (launch.py) 已在背景啟動 (PID: {launch_process.pid})。")

    # --- 步驟 4: 啟動前端智慧型渲染器 ---
    last_displayed_data = None
    try:
        while True:
            try:
                conn = sqlite3.connect(db_file)
                cursor = conn.cursor()
                cursor.execute("SELECT current_stage, apps_status, action_url, cpu_usage, ram_usage FROM status_table WHERE id = 1")
                status_row = cursor.fetchone()
                cursor.execute(f"SELECT timestamp, level, message FROM log_table ORDER BY id DESC LIMIT {config_data.get('LOG_DISPLAY_LINES', 10)}")
                log_rows = cursor.fetchall()
                conn.close()

                current_data = (status_row, log_rows)

                # 只有在資料變化時才重繪畫面
                if current_data != last_displayed_data:
                    clear_output(wait=True)
                    display(HTML(render_dashboard_html(status_row, log_rows, config_data)))
                    last_displayed_data = current_data

            except sqlite3.OperationalError as e:
                if "no such table" not in str(e):
                    # 忽略 "no such table" 錯誤，因為後端可能尚未建立好資料庫
                    pass

            time.sleep(config_data.get("REFRESH_RATE_SECONDS", 0.5))

    except KeyboardInterrupt:
        print("\n\n🛑 偵測到手動中斷！")
    finally:
        print("正在終止後端服務...")
        launch_process.terminate()
        try:
            launch_process.wait(timeout=5)
            print("✅ 後端服務已成功終止。")
        except subprocess.TimeoutExpired:
            print("⚠️ 後端服務未能及時回應終止信號，將強制終結。")
            launch_process.kill()
            print("✅ 後端服務已被強制終結。")

        # 執行報告歸檔
        archive_reports(project_path, LOG_ARCHIVE_FOLDER_NAME, TIMEZONE)

if __name__ == "__main__":
    main()
