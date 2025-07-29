# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 混合動力啟動器 v8.0 (終極版)                            ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       結合 GoTTY 的日誌即時性與 Web API 的結構化狀態更新，提供      ║
# ║       一個資訊豐富、反應迅速且極致穩定的監控與操作體驗。             ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心終極啟動器 v8.0 { vertical-output: true, display-mode: "form" }
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
import stat
from google.colab import output as colab_output

def main():
    try:
        base_path = Path("/content")
        project_path = base_path / PROJECT_FOLDER_NAME
        state_file_path = base_path / "phoenix_state.json"

        print("🚀 鳳凰之心終極啟動器 v8.0")
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
        # 安裝 GoTTY
        gotty_path = Path("/usr/local/bin/gotty")
        if not gotty_path.exists():
            print("   正在下載並安裝 GoTTY...")
            subprocess.run("wget -q https://github.com/yudai/gotty/releases/download/v1.0.1/gotty_linux_amd64.tar.gz -O gotty.tar.gz", shell=True, check=True)
            subprocess.run("tar -xzf gotty.tar.gz", shell=True, check=True)
            subprocess.run(["mv", "gotty", str(gotty_path)], check=True)
            gotty_path.chmod(gotty_path.stat().st_mode | stat.S_IEXEC) # 賦予執行權限
            print("   ✅ GoTTY 安裝完成。")
        # 安裝 Python 依賴
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "psutil", "pyyaml", "uv", "nest_asyncio", "httpx", "fastapi", "uvicorn"], check=True)
        print("✅ 核心依賴安裝完成。")

        # --- 步驟 3: 在背景啟動所有服務 ---
        print("\n3. 觸發背景服務啟動程序...")

        # 準備環境變數
        env = os.environ.copy()
        env["STATE_FILE"] = str(state_file_path)

        # 啟動 dashboard_api
        api_command = [sys.executable, "-m", "uvicorn", "apps.dashboard_api.main:app", "--port", "8004"]
        api_process = subprocess.Popen(api_command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ 儀表板 API 服務已在背景啟動 (PID: {api_process.pid})。")

        # 啟動 gotty 來執行 launch.py
        # 使用 --ws-origin='.*' 來允許任何來源的 WebSocket 連接，這在 Colab iframe 中是必需的
        gotty_command = ["gotty", "--ws-origin", ".*", "--port", "8080", "python", "launch.py"]
        gotty_process = subprocess.Popen(gotty_command, env=env, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"✅ GoTTY 日誌服務已在背景啟動 (PID: {gotty_process.pid})。")

        # --- 步驟 4: 自動偵測並顯示終極儀表板 ---
        print("\n4. 自動偵測並顯示終極儀表板...")
        dashboard_api_url = f"http://localhost:8004/" # dashboard_api 的根路徑
        max_retries = 15

        print("   正在等待儀表板 API 上線...")
        for i in range(max_retries):
            try:
                response = httpx.get(dashboard_api_url, timeout=1)
                if response.status_code == 200:
                    print(f"✅ 儀表板 API 已在第 {i+1} 秒偵測到！正在顯示...")
                    colab_output.serve_kernel_port_as_iframe(8004, height=800)
                    break
            except httpx.ConnectError:
                time.sleep(1)
            if i == max_retries - 1:
                print("❌ 儀表板 API 啟動超時。")

        # --- 步驟 5: 等待使用者手動終止 ---
        print("\n5. 所有服務已啟動。")
        print("   您可以隨時點擊 Colab 的「停止」按鈕來終止所有背景服務。")

        # 保持主腳本運行，以便背景服務可以持續
        try:
            while True:
                time.sleep(60)
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
