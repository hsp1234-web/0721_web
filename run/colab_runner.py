# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 終極啟動器 v7.0 (穩定版)                                ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       以最穩定、簡潔的方式準備環境，在背景啟動所有服務，然後使用     ║
# ║       官方推薦的 `google.colab.output` 函式庫，在輪詢探測成功後，    ║
# ║       自動顯示「唯讀監控儀表板」。監控儀表板會提供最終操作入口。      ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心全自動啟動器 v7.0 (穩定版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "4.1.2" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 日誌與報告設定**
#@markdown > **設定日誌歸檔的參數。**
#@markdown ---
#@markdown **日誌歸檔資料夾 (LOG_ARCHIVE_FOLDER_NAME)**
#@markdown > **留空即關閉歸檔功能。**
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}

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
import httpx
from google.colab import output as colab_output

def main():
    try:
        base_path = Path("/content")
        project_path = base_path / PROJECT_FOLDER_NAME
        log_file_path = project_path / "launch_logs.txt"

        print("🚀 鳳凰之心全自動化啟動程序 v7.0 (穩定版)")
        print("="*80)

        # --- 步驟 1: 準備專案 ---
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
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psutil", "pyyaml", "uv", "nest_asyncio", "httpx", "pytz"], check=True)
        print("✅ 核心依賴安裝完成。")

        # --- 步驟 3: 在背景啟動後端服務 ---
        print("\n3. 觸發背景服務啟動程序...")
        log_file = open(log_file_path, "w")
        server_process = subprocess.Popen([sys.executable, "launch.py"], stdout=log_file, stderr=subprocess.STDOUT)
        print(f"✅ 後端啟動腳本 (launch.py) 已在背景運行 (PID: {server_process.pid})。")

        # --- 步驟 4: 自動偵測並顯示監控儀表板 ---
        print("\n4. 自動偵測並顯示「唯讀監控儀表板」...")
        monitor_url = f"http://localhost:8000/" # 根路徑現在指向 monitor app
        max_retries = 20

        print("   正在等待監控儀表板上線...")
        for i in range(max_retries):
            try:
                response = httpx.get(monitor_url, timeout=1)
                if response.status_code == 200:
                    print(f"✅ 監控儀表板已在第 {i+1} 秒偵測到！正在顯示...")
                    colab_output.serve_kernel_port_as_iframe(8000, height=800)
                    break
            except httpx.ConnectError:
                time.sleep(1)
            if i == max_retries - 1:
                print("❌ 監控儀表板啟動超時。請檢查 `launch_logs.txt`。")

        # --- 步驟 5: 等待後端任務完成 ---
        try:
            print("\n5. 所有服務已在背景啟動。Colab 將等待服務手動終止...")
            print("   (您可以隨時點擊 Colab 的停止按鈕來手動終止所有服務)")
            server_process.wait()
            print("\n✅ 後端服務已正常終止。")
        except KeyboardInterrupt:
            print("\n\n🛑 偵測到手動中斷！正在強制終止所有背景服務...")
            server_process.terminate()
            server_process.wait()
            print("✅ 所有背景服務已被強制終止。")
        finally:
            log_file.close()
            # --- 步驟 6: 生成並歸檔報告 ---
            if LOG_ARCHIVE_FOLDER_NAME:
                print(f"\n6. 正在生成並歸檔執行報告至 '{LOG_ARCHIVE_FOLDER_NAME}'...")
                if 'core_utils' not in sys.path:
                     sys.path.append(str(project_path))
                from core_utils.report_generator import ReportGenerator
                archive_path = base_path / LOG_ARCHIVE_FOLDER_NAME
                generator = ReportGenerator(log_file_path=str(log_file_path), archive_folder=str(archive_path))
                generator.save()
            else:
                print("\n6. 已跳過日誌歸檔步驟。")

            print("\n🎉 所有任務已完成，儲存格已終止。🎉")

    except Exception as e:
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
