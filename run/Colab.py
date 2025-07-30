# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 鳳凰之心 - JS 驅動儀表板 v16.0.1                                ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   新架構：後端提供 API，前端 JS 自主渲染，徹底解決閃爍問題。       ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心 JS 啟動器 v16.0.1 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "6.0.1" #@param {type:"string"}
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
RUN_MODE = "完整部署模式 (Full-Deploy Mode)" #@param ["自動自檢模式 (Self-Check Mode)", "快速驗證模式 (Fast-Test Mode)", "完整部署模式 (Full-Deploy Mode)"]

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
import requests

# --- 動態安裝與匯入 ---
try:
    from IPython.display import display, HTML
except ImportError:
    print("正在安裝 'ipython'...")
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'ipython'], check=True)
    from IPython.display import display, HTML

try:
    from google.colab import output
except ImportError:
    print("⚠️  非 Colab 環境，將無法產生公開網址。")
    output = None # 提供一個假的 output 物件以免出錯

def main():
    # --- Part 0: 環境設定 ---
    base_path = Path(".")
    project_path = base_path / PROJECT_FOLDER_NAME
    db_file = project_path / "state.db"
    api_port = 8080 # 為 API 伺服器選擇一個埠號

    # --- 步驟 1: 準備專案 ---
    print("🚀 鳳凰之心 JS 驅動啟動器 v16.0.2")
    print("="*80)

    if FORCE_REPO_REFRESH and project_path.exists():
        print(f"強制刷新模式：正在刪除舊的專案資料夾 '{project_path}'...")
        shutil.rmtree(project_path)

    if not project_path.exists():
        print(f"正在從 {REPOSITORY_URL} 克隆專案...")
        subprocess.run(['git', 'clone', REPOSITORY_URL, str(project_path)], check=True)

    # 切換到專案目錄並指定特定分支/標籤
    os.chdir(project_path)
    print(f"工作目錄已切換至: {project_path}")
    print(f"正在切換到版本: {TARGET_BRANCH_OR_TAG}")
    subprocess.run(['git', 'fetch'], check=True)
    subprocess.run(['git', 'checkout', TARGET_BRANCH_OR_TAG], check=True)
    subprocess.run(['git', 'pull', 'origin', TARGET_BRANCH_OR_TAG], check=True)

    # 將專案根目錄加入 sys.path，這樣才能正確匯入 reporting 模組
    sys.path.append(str(project_path))
    import reporting

    # --- 步驟 2: 在背景啟動後端雙雄 ---
    print("\n2. 正在啟動後端服務...")

    # 準備環境變數
    env = os.environ.copy()
    env["PROJECT_DIR"] = str(base_path)
    env["DB_FILE"] = str(db_file)
    env["API_PORT"] = str(api_port)
    if "Fast-Test Mode" in RUN_MODE:
        env["FAST_TEST_MODE"] = "true"
    elif "Self-Check Mode" in RUN_MODE:
        env["SELF_CHECK_MODE"] = "true"

    # 建立日誌資料夾
    (project_path / "logs").mkdir(exist_ok=True)

    # 啟動主力部隊 (run.py)
    run_log_path = project_path / "logs" / "run.log"
    with open(run_log_path, "w") as f_run:
        run_process = subprocess.Popen(
            [sys.executable, "run.py"],
            env=env, stdout=f_run, stderr=subprocess.STDOUT
        )
    print(f"✅ 後端主力部隊 (run.py) 已在背景啟動 (PID: {run_process.pid})。")

    # 等待一下，讓 run.py 有時間建立資料庫
    print("等待 3 秒，讓主力部隊初始化資料庫...")
    time.sleep(3)

    # 啟動通訊官 (api_server.py)
    api_log_path = project_path / "logs" / "api_server.log"
    with open(api_log_path, "w") as f_api:
        api_process = subprocess.Popen(
            [sys.executable, "api_server.py"],
            env=env, stdout=f_api, stderr=subprocess.STDOUT
        )
    print(f"✅ 後端通訊官 (api_server.py) 已在背景啟動 (PID: {api_process.pid})。")

    # --- 步驟 3: 獲取 Colab 代理 URL 並渲染靜態舞台 ---
    print("\n3. 正在準備前端儀表板...")
    api_url = None
    if output:
        try:
            # 加入重試機制來穩定獲取 URL
            for i in range(5):
                url = output.eval_js(f'google.colab.kernel.proxyPort({api_port})')
                if url and url.startswith("https"):
                    api_url = url
                    break
                print(f"URL 獲取嘗試 {i+1}/5 失敗，等待 2 秒後重試...")
                time.sleep(2)
        except Exception as e:
            print(f"❌ 無法透過 google.colab.kernel.proxyPort 獲取 URL: {e}")

    if not api_url:
        print("❌ 無法獲取 Colab 代理 URL。儀表板可能無法正常工作。")
        # 即使無法獲取 URL，我們仍然繼續，以便可以查看日誌
    else:
        print(f"✅ 儀表板 API 將透過此 URL 訪問: {api_url}")

    # 健康檢查
    if api_url:
        is_healthy = False
        for i in range(10): # 最多等待 20 秒
            try:
                response = requests.get(f"{api_url}/api/health", timeout=2)
                if response.status_code == 200 and response.json().get("status") == "ok":
                    print(f"✅ 後端健康檢查通過！ ({i+1}/10)")
                    is_healthy = True
                    break
            except requests.RequestException as e:
                print(f"健康檢查嘗試 {i+1}/10 失敗: {e}")
            time.sleep(2)

        if not is_healthy:
            print("❌ 後端服務在超時後仍未通過健康檢查。請檢查 `logs/` 目錄下的日誌。")
            # 即使健康檢查失敗，也繼續執行以顯示儀表板，方便除錯

    # 讀取 HTML 模板並注入 API URL
    dashboard_template_path = project_path / "run" / "dashboard.html"
    with open(dashboard_template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    # 即使 api_url 為 None，也替換掉佔位符，避免前端出錯
    html_content = html_template.replace('{{ API_URL }}', api_url or '')

    # 顯示最終的靜態 HTML
    display(HTML(html_content))
    print("\n✅ 儀表板已載入。所有後續更新將由前端自主完成。")
    print(f"您可以查看 `{run_log_path}` 和 `{api_log_path}` 以獲取詳細日誌。")

    # --- 步驟 4: 等待手動中斷 ---
    try:
        print("\n後端服務正在運行中。您可以隨時在此儲存格按下「停止」按鈕來終止所有進程。")
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("\n\n🛑 偵測到手動中斷！")
    finally:
        print("\n正在終止後端服務...")
        # 溫和地終止
        api_process.terminate()
        run_process.terminate()
        try:
            api_process.wait(timeout=5)
            print("✅ API 伺服器已成功終止。")
        except subprocess.TimeoutExpired:
            api_process.kill()
            print("⚠️ API 伺服器被強制終結。")
        try:
            run_process.wait(timeout=5)
            print("✅ 主力部隊已成功終止。")
        except subprocess.TimeoutExpired:
            run_process.kill()
            print("⚠️ 主力部隊被強制終結。")

        print("\n正在產生最終報告...")
        try:
            reporting.create_final_reports()
            print("✅ 報告已成功生成。")
        except Exception as e:
            print(f"❌ 產生報告時發生錯誤: {e}")

if __name__ == "__main__":
    main()
