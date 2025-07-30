# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 鳳凰之心 - JS 驅動儀表板 v16.0 - 環境自適應版                 ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   新功能：可同時在 Colab 和標準環境中運行，並具備自我修復依賴能力。║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心 JS 啟動器 v16.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "4.5.8" #@param {type:"string"}
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

import os
import sys
import shutil
import subprocess
from pathlib import Path
import time
import datetime
import sqlite3

# --- 環境自適應與自我修復依賴 ---
def install_if_missing(package, import_name=None):
    """檢查套件是否存在，如果不存在則嘗試安裝"""
    try:
        __import__(import_name or package)
    except ImportError:
        print(f"缺少 '{package}' 套件，正在嘗試自動安裝...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", package], check=True)
            print(f"✅ 套件 '{package}' 安裝成功。")
            __import__(import_name or package)
        except Exception as e:
            print(f"❌ 自動安裝 '{package}' 失敗: {e}")
            # 根據情況決定是否要退出
            if package in ["pytz"]: # pytz 是報告功能的硬依賴
                sys.exit(1)

install_if_missing("pytz")
import pytz

IS_COLAB = 'google.colab' in sys.modules
if IS_COLAB:
    install_if_missing("IPython")
    from IPython.display import display, HTML
    from google.colab import output
else:
    # 在非 Colab 環境中，創建一個假的 display 和 output 物件，以避免 NameError
    class FakeDisplay:
        def display(self, *args, **kwargs): pass
        def HTML(self, *args, **kwargs): pass
    display = FakeDisplay()
    # output 物件不需要，因為我們用 IS_COLAB 來保護對它的呼叫

# --- 報告生成邏輯 ---
def generate_reports(project_path, db_file, start_time, end_time, stop_reason):
    # ... (此處省略與之前版本相同的報告生成程式碼)
    print("\n\n📊 正在生成最終報告...")

    tz = pytz.timezone('Asia/Taipei')
    timestamp = datetime.datetime.now(tz).strftime('%Y-%m-%d_%H-%M-%S')

    report_dir = project_path / "reports"
    report_dir.mkdir(exist_ok=True)

    logs_data = []
    final_status = {}
    if db_file.exists():
        try:
            conn = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
            conn.row_factory = sqlite3.Row
            logs_data = conn.execute("SELECT timestamp, level, message FROM log_table ORDER BY id ASC").fetchall()
            final_status_row = conn.execute("SELECT * FROM status_table WHERE id = 1").fetchone()
            if final_status_row:
                final_status = dict(final_status_row)
            conn.close()
        except Exception as e:
            print(f"無法從資料庫讀取報告數據: {e}")
    else:
        print("資料庫檔案不存在，無法生成報告。")
        return

    run_duration = end_time - start_time

    # --- 報告一：詳細日誌 ---
    log_report_path = report_dir / f"鳳凰之心報告_{timestamp}_詳細日誌.md"
    with open(log_report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 鳳凰之心 - 詳細日誌報告\n\n")
        f.write(f"**生成時間**: {datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"**運行總時長**: {run_duration}\n\n")
        f.write("```\n")
        if logs_data:
            for log in logs_data:
                f.write(f"[{log['timestamp']}] [{log['level']}] {log['message']}\n")
        else:
            f.write("沒有可用的日誌記錄。\n")
        f.write("```\n")

    # --- 報告二：詳細效能 ---
    perf_report_path = report_dir / f"鳳凰之心報告_{timestamp}_詳細效能.md"
    cpu_usage = final_status.get('cpu_usage', 0)
    ram_usage = final_status.get('ram_usage', 0)
    with open(perf_report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 鳳凰之心 - 詳細效能報告\n\n")
        f.write(f"**生成時間**: {datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n")
        f.write("## 最終資源快照\n")
        f.write(f"- **CPU 使用率**: {cpu_usage:.2f}%\n")
        f.write(f"- **記憶體使用率**: {ram_usage:.2f}%\n")

    # --- 報告三：綜合摘要 ---
    summary_report_path = report_dir / f"鳳凰之心報告_{timestamp}_綜合摘要.md"
    with open(summary_report_path, 'w', encoding='utf-8') as f:
        f.write(f"# 鳳凰之心 - 綜合摘要報告\n\n")
        f.write(f"- **報告生成時間**: {datetime.datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S %Z')}\n")
        f.write(f"- **運行總時長**: {run_duration}\n")
        f.write(f"- **終止原因**: {stop_reason}\n")
        f.write(f"- **最終階段**: `{final_status.get('current_stage', '未知')}`\n\n")
        f.write("## 效能摘要\n")
        f.write(f"- **最終 CPU**: {cpu_usage:.2f}%\n")
        f.write(f"- **最終 RAM**: {ram_usage:.2f}%\n\n")
        f.write("## 關鍵日誌 (錯誤與警告)\n")
        f.write("```\n")
        critical_logs = [log for log in logs_data if log['level'] in ('ERROR', 'CRITICAL', 'WARNING')]
        if critical_logs:
            for log in critical_logs:
                f.write(f"[{log['timestamp']}] [{log['level']}] {log['message']}\n")
        else:
            f.write("運行期間未記錄任何錯誤或警告。\n")
        f.write("```\n\n")
        f.write("## 詳細報告連結\n")
        f.write(f"- [詳細日誌](./{log_report_path.name})\n")
        f.write(f"- [詳細效能](./{perf_report_path.name})\n")

    print(f"✅ 報告已成功生成於 {report_dir.resolve()} 目錄下。")


# --- 主執行邏輯 ---
base_path = Path("/content") if 'google.colab' in sys.modules else Path.cwd()

def main():
    # ... (此處省略與之前版本相同的啟動和健康檢查程式碼)
    project_path = base_path / PROJECT_FOLDER_NAME
    db_file = project_path / "state.db"
    api_port = 8080

    print("🚀 鳳凰之心 JS 驅動啟動器 v16.0")
    print("="*80)
    print(f"ℹ️ 正在使用版本: {TARGET_BRANCH_OR_TAG}")
    if not project_path.exists():
        print(f"正在從 {REPOSITORY_URL} 克隆專案...")
        subprocess.run(['git', 'clone', REPOSITORY_URL, str(project_path)], check=True)
    os.chdir(project_path)
    print(f"工作目錄已切換至: {os.getcwd()}")

    print("\n2. 正在啟動後端服務...")
    env = os.environ.copy()
    env["DB_FILE"] = str(db_file)
    env["API_PORT"] = str(api_port)
    if "Fast-Test Mode" in RUN_MODE:
        env["FAST_TEST_MODE"] = "true"
    elif "Self-Check Mode" in RUN_MODE:
        env["SELF_CHECK_MODE"] = "true"

    launch_log = project_path / "logs" / "launch.log"
    launch_log.parent.mkdir(exist_ok=True)
    api_log = project_path / "logs" / "api_server.log"

    # 安裝 api_server.py 的相依性
    print("\n3. 正在準備後端通訊官...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "flask", "flask-cors"], check=True)
        print("✅ 後端通訊官相依性 (Flask, Flask-CORS) 已確認或安裝。")
    except subprocess.CalledProcessError as e:
        print(f"❌ 無法安裝後端通訊官的相依性: {e}")
        raise RuntimeError("相依性安裝失敗") from e

    f_launch = open(launch_log, "w")
    launch_process = subprocess.Popen([sys.executable, "launch.py"], env=env, stdout=f_launch, stderr=subprocess.STDOUT)
    print(f"✅ 後端主力部隊 (launch.py) 已在背景啟動 (PID: {launch_process.pid})。")

    f_api = open(api_log, "w")
    api_process = subprocess.Popen([sys.executable, "api_server.py"], env=env, stdout=f_api, stderr=subprocess.STDOUT)
    print(f"✅ 後端通訊官 (api_server.py) 已在背景啟動 (PID: {api_process.pid})。")

    print("\n4. 正在執行後端健康檢查...")
    health_check_url = f"http://localhost:{api_port}/api/health"
    is_healthy = False
    for i in range(20):
        try:
            result = subprocess.run(['curl', '-s', health_check_url], capture_output=True, text=True, timeout=1)
            if result.returncode == 0 and '"status": "ok"' in result.stdout:
                print("✅ 後端健康檢查通過！服務已就緒。")
                is_healthy = True
                break
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        time.sleep(0.5)

    if not is_healthy:
        print("❌ 後端服務在超時後仍未通過健康檢查。請檢查 `logs/api_server.log`。")
        raise RuntimeError("後端服務啟動失敗")

    print("\n5. 正在準備前端儀表板...")
    if IS_COLAB:
        api_url = None
        for i in range(5):
            try:
                url = output.eval_js(f'google.colab.kernel.proxyPort({api_port})')
                if url and url.startswith("https"):
                    api_url = url
                    break
            except Exception:
                pass
            time.sleep(1)

        if not api_url:
            print("❌ 經過多次嘗試後，仍無法獲取 Colab 代理 URL。儀表板可能無法正常工作。")
        else:
            print(f"✅ 儀表板 API 將透過此 URL 訪問: {api_url}")
            dashboard_template_path = Path("run") / "dashboard.html"
            with open(dashboard_template_path, 'r', encoding='utf-8') as f:
                html_template = f.read()
            html_content = html_template.replace('{{ API_URL }}', api_url)
            display(HTML(html_content))
            print("\n✅ 儀表板已載入。所有後續更新將由前端自主完成。")
    else:
        print("ℹ️ 非 Colab 環境，跳過儀表板渲染。可透過 http://localhost:8080 訪問 API。")

    print("您可以查看 `logs/` 目錄下的 launch.log 和 api_server.log 以獲取詳細日誌。")

    start_time = datetime.datetime.now()
    stop_reason = "未知"
    try:
        print("\n後端服務正在運行中。您可以隨時在此儲存格按下「停止」按鈕來終止所有進程。")
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        stop_reason = "偵測到手動中斷"
        print(f"\n\n🛑 {stop_reason}！")
    except Exception as e:
        stop_reason = f"發生未預期錯誤: {e}"
        print(f"\n\n💥 {stop_reason}")
    finally:
        end_time = datetime.datetime.now()
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

        f_launch.close()
        f_api.close()

        generate_reports(project_path, db_file, start_time, end_time, stop_reason)

if __name__ == "__main__":
    main()
