# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab GoTTY 混合動力啟動器 v10.0 (診斷版)                       ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       一個絕對可靠的啟動器，不僅要能工作，還要能在失敗時提供清晰的   ║
# ║       診斷資訊，確保使用者總能了解系統的真實狀態。                   ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心終極啟動器 v10.0 { vertical-output: true, display-mode: "form" }
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
#@markdown ### **Part 2: 除錯設定**
#@markdown > **啟用後，將顯示所有詳細日誌，用於問題診斷。**
#@markdown ---
#@markdown **開啟除錯模式 (DEBUG_MODE)**
DEBUG_MODE = True #@param {type:"boolean"}
#@markdown **快速測試模式 (FAST_TEST_MODE)**
#@markdown > 預設開啟。將跳過所有 App 的依賴安裝和啟動，用於快速驗證核心通訊流程。取消勾選以執行完整的真實部署。
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
import stat
import httpx
from IPython.display import display, HTML, Javascript

def main():
    try:
        base_path = Path("/content")
        project_path = base_path / PROJECT_FOLDER_NAME
        state_file_path = project_path / "phoenix_state.json"

        print("🚀 鳳凰之心終極啟動器 v10.0")
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

        # --- 步驟 2: 安裝 GoTTY 和核心依賴 ---
        print("\n2. 安裝 GoTTY 和核心 Python 依賴...")
        gotty_path = Path("/usr/local/bin/gotty")
        if not gotty_path.exists():
            print("   正在下載並安裝 GoTTY...")
            subprocess.run("wget -q https://github.com/yudai/gotty/releases/download/v1.0.1/gotty_linux_amd64.tar.gz -O gotty.tar.gz", shell=True, check=True)
            subprocess.run("tar -xzf gotty.tar.gz", shell=True, check=True)
            subprocess.run(["mv", "gotty", str(gotty_path)], check=True)
            gotty_path.chmod(gotty_path.stat().st_mode | stat.S_IEXEC)
        print("   ✅ GoTTY 已就緒。")
        print("   - 正在安裝所有 App 的依賴項到主環境...")
        all_reqs_path = project_path / "all_requirements.txt"
        # 合併所有 requirements.txt
        with open(all_reqs_path, "w") as outfile:
            for app_dir in (project_path / "apps").iterdir():
                if app_dir.is_dir():
                    req_file = app_dir / "requirements.txt"
                    if req_file.exists():
                        with open(req_file) as infile:
                            outfile.write(infile.read())
                        outfile.write("\n")

        # 升級 pip
        print("   - 正在升級 pip...")
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # 安裝所有依賴 + 核心依賴
        print("   - 正在安裝所有 App 的依賴項...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(all_reqs_path)], check=True)
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "rich", "uvicorn", "httpx"], check=True)
        print("✅ 所有依賴安裝完成。")

        # --- 步驟 3: 在背景啟動所有服務 ---
        print("\n3. 觸發背景服務啟動程序...")
        env = os.environ.copy()
        env["STATE_FILE"] = str(state_file_path)
        if FAST_TEST_MODE:
            env["FAST_TEST_MODE"] = "true"
            print("\n🚀 快速測試模式已啟用。")

        # 根據除錯模式決定輸出目標
        stdout_target = subprocess.DEVNULL
        if DEBUG_MODE:
            print("\n🔍 除錯模式已啟用，所有日誌將被記錄。")
            log_dir = project_path / "logs"
            log_dir.mkdir(exist_ok=True)
            api_log_path = log_dir / "api.log"
            gotty_log_path = log_dir / "gotty.log"
            stdout_target = open(api_log_path, "w")
            gotty_stdout_target = open(gotty_log_path, "w")
            print(f"   - API 服務日誌將寫入: {api_log_path}")
            print(f"   - GoTTY/Launch.py 日誌將寫入: {gotty_log_path}")
        else:
            gotty_stdout_target = subprocess.DEVNULL


        api_command = [sys.executable, "-m", "uvicorn", "apps.dashboard_api.main:app", "--port", "8004", "--host", "0.0.0.0"]
        api_process = subprocess.Popen(api_command, env=env, stdout=stdout_target, stderr=subprocess.STDOUT)
        print(f"✅ 儀表板 API 服務已在背景啟動 (PID: {api_process.pid})。")

        gotty_command = ["gotty", "--ws-origin", ".*", "-w", "--port", "8080", sys.executable, "launch.py"]
        gotty_process = subprocess.Popen(gotty_command, env=env, stdout=gotty_stdout_target, stderr=subprocess.STDOUT)
        print(f"✅ GoTTY 日誌服務已在背景啟動 (PID: {gotty_process.pid})。")

        # --- 步驟 4: 顯示 GoTTY 並啟動後端輪詢 ---
        print("\n4. 正在載入 GoTTY 日誌儀表板...")
        from google.colab import output
        import httpx

        placeholder_html = HTML("<div id='action-button-placeholder'></div>")
        display(placeholder_html)

        output.serve_kernel_port_as_iframe(8080, height=600)

        # --- 步驟 5: 後端輪詢 API 並動態生成操作按鈕 ---
        print("\n5. 啟動後端輪詢程序，等待儀表板 URL 就緒...")
        api_url = "http://localhost:8004/api/get-action-url"
        max_retries = 30 # 延長重試次數以應對較慢的啟動

        final_url = None
        for i in range(max_retries):
            print(f"   🔄 正在嘗試獲取操作連結... (第 {i+1}/{max_retries} 次)")
            try:
                with httpx.Client() as client:
                    response = client.get(api_url, timeout=5)
                if response.status_code == 200:
                    data = response.json()
                    if data.get("status") == "success" and data.get("url"):
                        final_url = data["url"]
                        print(f"✅ 成功獲取儀表板 URL: {final_url}")
                        break
            except httpx.RequestError:
                pass
            time.sleep(5)

        # --- 步驟 6: 根據輪詢結果更新前端 ---
        if final_url:
            js_code = f'''
                const placeholder = document.getElementById('action-button-placeholder');
                placeholder.innerHTML = `<br><a href="{final_url}" target="_blank" style="display:inline-block; padding: 15px 30px; background-color: #007bff; color: white; text-decoration: none; font-size: 18px; border-radius: 8px;">🚀 點此開啟主操作儀表板 🚀</a>`;
            '''
            display(Javascript(js_code))
            print("\n✅ 操作按鈕已成功顯示在上方。")
        else:
            js_code = """
                const placeholder = document.getElementById('action-button-placeholder');
                placeholder.innerHTML = `<br><p style="color: red;">❌ 獲取操作連結超時，請檢查 GoTTY 日誌儀表板中的錯誤訊息。</p>`;
            """
            display(Javascript(js_code))
            print("\n❌ 獲取儀表板 URL 失敗。")

        # --- 步驟 7: 等待使用者手動終止 ---
        print("\n\n所有服務已啟動。您可以透過上方 GoTTY 視窗查看即時日誌。")
        try:
            while True: time.sleep(60)
        except KeyboardInterrupt:
            print("\n\n🛑 偵測到手動中斷！正在終止所有背景服務...")
            api_process.terminate()
            gotty_process.terminate()
            print("✅ 所有背景服務已被終止。")

    except Exception as e:
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
