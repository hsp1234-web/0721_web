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
TARGET_BRANCH_OR_TAG = "6.0.2" #@param {type:"string"}
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
    base_path = Path(".").resolve() # 獲取當前工作目錄的絕對路徑
    project_path = base_path / PROJECT_FOLDER_NAME

    # --- 步驟 1: 準備專案 ---
    print("🚀 鳳凰之心 JS 驅動啟動器 v16.0.6")
    print("="*80)

    # 在切換目錄前，先處理根目錄下的操作
    if FORCE_REPO_REFRESH and project_path.exists():
        print(f"強制刷新模式：正在刪除舊的專案資料夾 '{project_path}'...")
        shutil.rmtree(project_path)

    if not project_path.exists():
        print(f"正在從 {REPOSITORY_URL} 克隆專案...")
        result = subprocess.run(['git', 'clone', REPOSITORY_URL, str(project_path)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Git clone 失敗：\n{result.stderr}")
            return

    # 在 chdir 之前定義好所有路徑
    db_file = project_path / "state.db"
    api_port = 8080

    # --- 步驟 2: 啟動後端服務 ---
    print("\n2. 正在啟動後端服務...")

    # **關鍵修正**: 在啟動服務前，先建立 logs 資料夾
    (project_path / "logs").mkdir(exist_ok=True)
    print(f"✅ 已在 {project_path} 中確保 logs 資料夾存在。")

    # 準備環境變數
    env = os.environ.copy()
    env["DB_FILE"] = str(db_file)
    env["API_PORT"] = str(api_port)
    if "Fast-Test Mode" in RUN_MODE:
        env["FAST_TEST_MODE"] = "true"
    elif "Self-Check Mode" in RUN_MODE:
        env["SELF_CHECK_MODE"] = "true"

    # 啟動主力部隊 (run.py) - **關鍵修正**: 使用 project_path 作為 cwd
    run_log_path = project_path / "logs" / "run.log"
    with open(run_log_path, "w") as f_run:
        run_process = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=str(project_path), env=env, stdout=f_run, stderr=subprocess.STDOUT
        )
    print(f"✅ 後端主力部隊 (run.py) 已在背景啟動 (PID: {run_process.pid})。")

    print("等待 3 秒，讓主力部隊初始化資料庫...")
    time.sleep(3)

    # 啟動通訊官 (api_server.py) - **關鍵修正**: 使用 project_path 作為 cwd
    api_log_path = project_path / "logs" / "api_server.log"
    with open(api_log_path, "w") as f_api:
        api_process = subprocess.Popen(
            [sys.executable, "api_server.py"],
            cwd=str(project_path), env=env, stdout=f_api, stderr=subprocess.STDOUT
        )
    print(f"✅ 後端通訊官 (api_server.py) 已在背景啟動 (PID: {api_process.pid})。")

    # --- 步驟 3: 獲取 Colab 代理 URL 並渲染靜態舞台 ---
    print("\n3. 正在準備前端儀表板...")
    api_url = None
    if output:
        try:
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
    else:
        print(f"✅ 儀表板 API 將透過此 URL 訪問: {api_url}")

    # 健康檢查
    if api_url:
        is_healthy = False
        for i in range(10):
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

    # 讀取 HTML 模板並注入 API URL
    dashboard_template_path = project_path / "run" / "dashboard.html"
    with open(dashboard_template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

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

        print("\n正在移動報告資料夾...")
        source_report_dir = project_path / "報告"
        dest_report_dir = base_path / "報告"
        if source_report_dir.exists():
            try:
                if dest_report_dir.exists():
                    shutil.copytree(str(source_report_dir), str(dest_report_dir), dirs_exist_ok=True)
                    shutil.rmtree(source_report_dir)
                else:
                    shutil.move(str(source_report_dir), str(dest_report_dir))
                print(f"✅ 報告資料夾已成功處理。最終位置: {dest_report_dir.resolve()}")
            except Exception as e:
                print(f"❌ 處理報告資料夾時發生錯誤: {e}")
        else:
            print("⚠️ 找不到由後端生成的報告資料夾，無需移動。")

if __name__ == "__main__":
    main()
