# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║      🚀 Colab 資料庫驅動儀表板 v12.0 (穩定版)                        ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       一個絕對穩定的架構，將「做事」與「顯示」徹底分離。後端專心     ║
# ║       更新資料庫，前端專心讀取資料庫並渲染，互不干擾。               ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心資料庫啟動器 v12.0 { vertical-output: true, display-mode: "form" }
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
from IPython.display import display, HTML, Javascript, clear_output

def main():
    # --- 全域路徑與變數 ---
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME
    db_file = project_path / "state.db"

    # --- 步驟 1: 準備專案 ---
    print("🚀 鳳凰之心資料庫啟動器 v12.0")
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
    # 升級 pip
    subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # 安裝所有 App 的依賴
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
            env=env,
            stdout=f,
            stderr=subprocess.STDOUT
        )
    print(f"✅ 後端主力部隊 (launch.py) 已在背景啟動 (PID: {launch_process.pid})。")
    print(f"   - 日誌將寫入: {log_file}")

    # --- 步驟 4: 啟動前端戰情顯示器 ---
    print("\n4. 正在啟動前端戰情顯示器...")
    time.sleep(2) # 等待資料庫初始化

    try:
        while True:
            clear_output(wait=True)
            conn = sqlite3.connect(db_file)
            cursor = conn.cursor()

            # 讀取狀態
            cursor.execute("SELECT current_stage, apps_status, action_url, cpu_usage, ram_usage FROM status_table WHERE id = 1")
            status_row = cursor.fetchone()

            # 讀取日誌
            cursor.execute("SELECT timestamp, level, message FROM log_table ORDER BY id DESC LIMIT 10")
            log_rows = cursor.fetchall()

            conn.close()

            if not status_row:
                print("⏳ 等待資料庫狀態初始化...")
                time.sleep(1)
                continue

            stage, apps_status_json, action_url, cpu, ram = status_row
            apps_status = json.loads(apps_status_json) if apps_status_json else {}

            # --- 繪製儀表板 ---
            print("╔══════════════════════════════════════════════════════════════════════════════╗")
            print("║                          🚀 鳳凰之心 - 作戰指揮中心 🚀                          ║")
            print("╠══════════════════════════════════════════════════════════════════════════════╣")
            print(f"║ 狀態: {stage.upper():<15} | CPU: {cpu or 0.0:>5.1f}% | RAM: {ram or 0.0:>5.1f}%             ║")
            print("╠═══════════════════════════╤══════════════════════════════════════════════════╣")
            print("║         服務狀態          │                   即時日誌 (最新 10 筆)              ║")
            print("╟───────────────────────────┘                                                  ║")

            app_lines = []
            for app, status in apps_status.items():
                status_map = {"pending": "⚪", "starting": "🟡", "running": "🟢", "failed": "🔴"}
                icon = status_map.get(status, "❓")
                app_lines.append(f"║ {icon} {app.capitalize():<25} ║")

            for i in range(10):
                app_line = app_lines[i] if i < len(app_lines) else "║" + " "*27 + "║"
                log_line = log_rows[i] if i < len(log_rows) else ("", "", "")
                ts, level, msg = log_line
                ts_str = str(ts).split(" ")[1][:8] if ts else ""
                log_text = f" {ts_str} [{level}] {msg}"
                print(f"{app_line}{log_text:<57}║")

            print("╚══════════════════════════════════════════════════════════════════════════════╝")

            if action_url:
                print(f"\n✅ 啟動完成！點擊以下連結開啟主操作儀表板：")
                print(f"   👉 {action_url}")
                break # 結束迴圈

            if stage in ["failed", "critical_failure"]:
                print("\n❌ 啟動失敗。請檢查日誌以了解詳情。")
                break

            time.sleep(1)

    except KeyboardInterrupt:
        print("\n\n🛑 偵測到手動中斷！正在終止後端服務...")
        launch_process.terminate()
        print("✅ 後端服務已被終止。")
    except Exception as e:
        print(f"\n💥 前端顯示器發生未預期的嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
