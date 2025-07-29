# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 全自動化啟動器 v4.0                                     ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       以最快速度準備並啟動後端 Web 儀表板，然後在 Colab 端透過      ║
# ║       JavaScript 自動偵測並嵌入儀表板畫面。任務結束後，自動生成      ║
# ║       精美的 Markdown 報告並歸檔，最後自動終止儲存格。             ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心全自動啟動器 v4.0 { vertical-output: true, display-mode: "form" }
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
from IPython.display import display, Javascript, HTML

def main():
    try:
        base_path = Path("/content")
        project_path = base_path / PROJECT_FOLDER_NAME
        log_file_path = project_path / "launch_logs.txt"

        print("🚀 鳳凰之心全自動化啟動程序 v4.0")
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

        # --- 步驟 4: 自動偵測並顯示儀表板 ---
        print("\n4. 自動偵測並嵌入 Web 監控儀表板...")
        proxy_url = "http://localhost:8000"

        # 使用 Javascript 來實現自動重試和嵌入 iframe
        js_code = f"""
            const url = '{proxy_url}';
            const maxRetries = 20; // 最多重試 20 次 (共 20 秒)
            let retries = 0;
            const intervalId = setInterval(async () => {{
                const statusDiv = document.getElementById('status');
                try {{
                    const response = await fetch(url, {{ mode: 'no-cors' }});
                    // 對於 no-cors 模式，我們無法檢查 status，但只要請求不拋出錯誤就認為服務已上線
                    clearInterval(intervalId);
                    statusDiv.innerHTML = `<h2>✅ 儀表板已上線！正在載入...</h2>`;

                    const iframe = document.createElement('iframe');
                    iframe.src = url;
                    iframe.style.width = '100%';
                    iframe.style.height = '600px';
                    iframe.style.border = '1px solid #ccc';
                    document.getElementById('dashboard').appendChild(iframe);

                }} catch (e) {{
                    retries++;
                    statusDiv.innerHTML = `<h2>⏳ 等待儀表板上線中... (嘗試第 ${{retries}} 次)</h2>`;
                    if (retries >= maxRetries) {{
                        clearInterval(intervalId);
                        statusDiv.innerHTML = `<h2>❌ 儀表板啟動超時，請檢查日誌。</h2>`;
                    }}
                }}
            }}, 1000);
        """
        display(HTML('<div id="status"></div><div id="dashboard"></div>'))
        display(Javascript(js_code))

        # --- 步驟 5: 等待後端任務完成 ---
        print("\n5. Colab 前端將在背景監測後端任務，完成後將自動生成報告並終止。")
        server_process.wait() # 等待 launch.py 執行緒結束
        log_file.close() # 關閉日誌檔案
        print("\n✅ 後端服務已終止。")

        # --- 步驟 6: 生成並歸檔報告 ---
        if LOG_ARCHIVE_FOLDER_NAME:
            print(f"\n6. 正在生成並歸檔執行報告至 '{LOG_ARCHIVE_FOLDER_NAME}'...")
            from core_utils.report_generator import ReportGenerator
            # 注意：這裡的歸檔路徑是在 Colab 的根目錄，而不是專案目錄內
            archive_path = base_path / LOG_ARCHIVE_FOLDER_NAME
            generator = ReportGenerator(log_file_path=str(log_file_path), archive_folder=str(archive_path))
            generator.save()
        else:
            print("\n6. 已跳過日誌歸檔步驟。")

        print("\n🎉 所有任務已完成，儲存格將自動終止。🎉")

    except Exception as e:
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
