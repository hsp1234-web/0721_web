# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 鳳凰之心 - JS 驅動儀表板 v15.0                                ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   新架構：後端提供 API，前端 JS 自主渲染，徹底解決閃爍問題。       ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心 JS 啟動器 v15.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "4.3.9" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}
#@markdown ---
#@markdown ### **Part 2: 模式設定**
#@markdown > **用於快速驗證或完整部署。**
#@markdown ---
#@markdown **運行模式 (RUN_MODE)**
#@markdown > 選擇啟動器的運行模式。
RUN_MODE = "自動自檢模式 (Self-Check Mode)" #@param ["自動自檢模式 (Self-Check Mode)", "快速驗證模式 (Fast-Test Mode)", "完整部署模式 (Full-Deploy Mode)"]

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
from IPython.display import display, HTML
from google.colab import output

def main():
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME
    db_file = project_path / "state.db"
    api_port = 8080 # 為 API 伺服器選擇一個埠號

    # --- 步驟 1: 準備專案 (與之前版本類似) ---
    print("🚀 鳳凰之心 JS 驅動啟動器 v15.0")
    print("="*80)
    # ... (此處省略了與之前版本相同的 Git clone/pull 邏輯)
    # 為了簡潔，我們假設程式碼已經存在於 project_path
    if not project_path.exists():
        print(f"正在從 {REPOSITORY_URL} 克隆專案...")
        subprocess.run(['git', 'clone', REPOSITORY_URL, str(project_path)], check=True)
    os.chdir(project_path)
    print(f"工作目錄已切換至: {os.getcwd()}")


    # --- 步驟 2: 在背景啟動後端雙雄 ---
    print("\n2. 正在啟動後端服務...")

    # 設定環境變數
    env = os.environ.copy()
    env["DB_FILE"] = str(db_file)
    env["API_PORT"] = str(api_port)
    if "Fast-Test Mode" in RUN_MODE:
        env["FAST_TEST_MODE"] = "true"
    elif "Self-Check Mode" in RUN_MODE:
        env["SELF_CHECK_MODE"] = "true"

    # 啟動主力部隊 (launch.py)
    launch_log = project_path / "logs" / "launch.log"
    launch_log.parent.mkdir(exist_ok=True)
    with open(launch_log, "w") as f_launch:
        launch_process = subprocess.Popen([sys.executable, "launch.py"], env=env, stdout=f_launch, stderr=subprocess.STDOUT)
    print(f"✅ 後端主力部隊 (launch.py) 已在背景啟動 (PID: {launch_process.pid})。")

    # 啟動通訊官 (api_server.py)
    api_log = project_path / "logs" / "api_server.log"
    with open(api_log, "w") as f_api:
        api_process = subprocess.Popen([sys.executable, "api_server.py"], env=env, stdout=f_api, stderr=subprocess.STDOUT)
    print(f"✅ 後端通訊官 (api_server.py) 已在背景啟動 (PID: {api_process.pid})。")

    # --- 步驟 3: 獲取 Colab 代理 URL 並渲染靜態舞台 ---
    print("\n3. 正在準備前端儀表板...")

    # 獲取 Colab 為 API 伺服器分配的 URL，並加入重試機制
    api_url = None
    for i in range(5): # 最多嘗試 5 次
        try:
            url = output.eval_js(f'google.colab.kernel.proxyPort({api_port})')
            if url and url.startswith("https"):
                api_url = url
                break
            print(f"URL 獲取嘗試 {i+1}/5 失敗，返回值無效: {url}")
        except Exception as e:
            print(f"URL 獲取嘗試 {i+1}/5 失敗，發生異常: {e}")

        if i < 4:
            print("等待 2 秒後重試...")
            time.sleep(2)

    if not api_url:
        print("❌ 經過多次嘗試後，仍無法獲取 Colab 代理 URL。儀表板可能無法正常工作。")
        return

    print(f"✅ 儀表板 API 將透過此 URL 訪問: {api_url}")

    # 讀取 HTML 模板 (使用相對路徑，因為我們已經 chdir)
    dashboard_template_path = Path("run") / "dashboard.html"
    with open(dashboard_template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # 注入 API URL
    html_content = html_template.replace('{{ API_URL }}', api_url)

    # 顯示最終的靜態 HTML
    display(HTML(html_content))
    print("\n✅ 儀表板已載入。所有後續更新將由前端自主完成。")
    print("您可以查看 `logs/` 目錄下的 launch.log 和 api_server.log 以獲取詳細日誌。")

    # --- 步驟 4: 等待手動中斷 ---
    try:
        print("\n後端服務正在運行中。您可以隨時在此儲存格按下「停止」按鈕來終止所有進程。")
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n🛑 偵測到手動中斷！")
    finally:
        print("正在終止後端服務...")
        api_process.terminate()
        launch_process.terminate()
        try:
            api_process.wait(timeout=5)
            print("✅ API 伺服器已成功終止。")
        except subprocess.TimeoutExpired:
            api_process.kill()
            print("⚠️ API 伺服器被強制終結。")
        try:
            launch_process.wait(timeout=5)
            print("✅ 主力部隊已成功終止。")
        except subprocess.TimeoutExpired:
            launch_process.kill()
            print("⚠️ 主力部隊被強制終結。")

if __name__ == "__main__":
    main()
