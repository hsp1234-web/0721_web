# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 鳳凰之心 - JS 驅動儀表板 v17.1.0                                ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   架構最終版：穩定工作目錄，根治競爭條件，提升整體可靠性。         ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心 JS 啟動器 v17.1.0 { vertical-output: true, display-mode: "form" }
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

def install_and_import(package):
    """動態安裝套件並回傳模組"""
    try:
        return __import__(package)
    except ImportError:
        print(f"正在安裝 '{package}'...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', package], check=True)
        return __import__(package)

def main():
    # --- Part 0: 環境與路徑設定 (根治競爭條件問題) ---
    # **關鍵修正**: 腳本一開始就切換到一個絕對且穩定的工作目錄
    stable_base_path = Path("/content").resolve()
    os.chdir(stable_base_path)
    print(f"✅ 工作目錄已穩定在: {os.getcwd()}")

    project_path = stable_base_path / PROJECT_FOLDER_NAME

    # --- 步驟 1: 準備專案 ---
    print("\n🚀 鳳凰之心 JS 驅動啟動器 v17.1.0")
    print("="*80)

    if FORCE_REPO_REFRESH and project_path.exists():
        print(f"強制刷新模式：正在刪除舊的專案資料夾 '{project_path}'...")
        shutil.rmtree(project_path)

    if not project_path.exists():
        print(f"正在從 {REPOSITORY_URL} 克隆專案至 {project_path}...")
        # 在穩定的 /content 目錄下執行 git clone
        result = subprocess.run(['git', 'clone', REPOSITORY_URL, str(project_path)], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"❌ Git clone 失敗：\n{result.stderr}")
            return

    db_file = project_path / "state.db"
    api_port = 8080

    # --- 步驟 2: 預先獲取初始數據 & 渲染儀表板 ---
    print("\n2. 正在準備即時儀表板...")

    psutil = install_and_import('psutil')
    requests = install_and_import('requests')

    initial_cpu = psutil.cpu_percent()
    initial_ram = psutil.virtual_memory().percent
    print(f"✅ 已獲取初始數據: CPU {initial_cpu:.1f}%, RAM {initial_ram:.1f}%")

    dashboard_template_path = project_path / "run" / "dashboard.html"
    with open(dashboard_template_path, 'r', encoding='utf-8') as f:
        html_template = f.read()

    html_content = html_template.replace('{{ INITIAL_CPU }}', f"{initial_cpu:.1f}%")
    html_content = html_content.replace('{{ INITIAL_RAM }}', f"{initial_ram:.1f}%")

    from IPython.display import display, HTML
    display(HTML(html_content))
    print("✅ 儀表板已載入初始數據，後端服務即將啟動...")

    # --- 步驟 3: 啟動後端服務 ---
    print("\n3. 正在啟動後端服務...")

    (project_path / "logs").mkdir(exist_ok=True)

    env = os.environ.copy()
    env["DB_FILE"] = str(db_file)
    env["API_PORT"] = str(api_port)
    if "Fast-Test Mode" in RUN_MODE: env["FAST_TEST_MODE"] = "true"
    if "Self-Check Mode" in RUN_MODE: env["SELF_CHECK_MODE"] = "true"

    run_log_path = project_path / "logs" / "run.log"
    with open(run_log_path, "w") as f_run:
        run_process = subprocess.Popen(
            [sys.executable, "run.py"],
            cwd=str(project_path), env=env, stdout=f_run, stderr=subprocess.STDOUT
        )
    print(f"✅ 後端主力部隊 (run.py) 已在背景啟動 (PID: {run_process.pid})。")

    time.sleep(3)

    api_log_path = project_path / "logs" / "api_server.log"
    with open(api_log_path, "w") as f_api:
        api_process = subprocess.Popen(
            [sys.executable, "api_server.py"],
            cwd=str(project_path), env=env, stdout=f_api, stderr=subprocess.STDOUT
        )
    print(f"✅ 後端通訊官 (api_server.py) 已在背景啟動 (PID: {api_process.pid})。")

    # --- 步驟 4: 獲取 API URL 並觸發前端輪詢 ---
    print("\n4. 正在連接前端與後端...")
    api_url = None
    try:
        from google.colab import output
        for i in range(5):
            url = output.eval_js(f'google.colab.kernel.proxyPort({api_port})')
            if url and url.startswith("https"):
                api_url = url
                break
            time.sleep(2)
    except (ImportError, AttributeError):
        print("⚠️ 非 Colab 環境，無法獲取公開 URL。")

    if not api_url:
        print("❌ 無法獲取 Colab 代理 URL，後續更新可能失敗。")
    else:
        print(f"✅ 後端 API 將透過此 URL 訪問: {api_url}")
        js_code = f"""
        <script>
            const dashboardElement = document.getElementById('dashboard-container');
            dashboardElement.dataset.apiUrl = '{api_url}';
            dashboardElement.dispatchEvent(new CustomEvent('startPolling'));
        </script>
        """
        display(HTML(js_code))
        print("✅ 已觸發前端輪詢機制。")

    # --- 步驟 5: 等待手動中斷 ---
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
        dest_report_dir = stable_base_path / "報告"
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
