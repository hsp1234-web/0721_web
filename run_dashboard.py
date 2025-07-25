#@title 💎 鳳凰之心整合式指揮中心 v14.0 (後端驅動版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **1. 顯示偏好設定**
#@markdown > **在啟動前，設定您的戰情室顯示偏好。**
#@markdown ---
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
#@markdown > **設定駕駛艙資訊流中最多顯示的日誌行數。**
LOG_DISPLAY_LINES = 100 #@param {type:"integer"}
#@markdown **狀態刷新頻率 (秒) (STATUS_REFRESH_INTERVAL)**
#@markdown > **設定後端採集並推送 CPU/RAM 狀態的間隔，可為小數。**
STATUS_REFRESH_INTERVAL = 0.5 #@param {type:"number"}

#@markdown ---
#@markdown ### **2. 專案路徑與伺服器設定**
#@markdown > **請指定要執行後端程式碼的資料夾名稱。**
#@markdown ---
#@markdown **指定專案資料夾名稱 (TARGET_FOLDER_NAME)**
#@markdown > **請輸入包含您後端程式碼 (例如 `main.py`) 的資料夾名稱。例如：`WEB`。**
TARGET_FOLDER_NAME = "WEB" #@param {type:"string"}
#@markdown **日誌歸檔資料夾 (ARCHIVE_FOLDER_NAME)**
#@markdown > **最終的 .txt 日誌報告將儲存於此獨立的中文資料夾。**
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **後端服務埠號 (FASTAPI_PORT)**
#@markdown > **後端 FastAPI 應用程式監聽的埠號。**
FASTAPI_PORT = 8000 #@param {type:"integer"}
#@markdown ---
#@markdown > **準備就緒後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# SECTION 0: 環境初始化與核心模組導入
# ==============================================================================
import os
import sys
import subprocess
import time
from pathlib import Path
from IPython.display import display, HTML, Javascript

# ==============================================================================
# SECTION 1: 核心啟動流程
# ==============================================================================
server_process = None

try:
    # --- 步驟 1: 清理並準備顯示區域 ---
    # 使用 JavaScript 清理先前可能存在的輸出，確保介面乾淨
    display(Javascript("document.querySelectorAll('.phoenix-launcher-output').forEach(el => el.remove());"))
    time.sleep(0.2)

    # 建立一個唯一的容器 ID，用於嵌入 iframe
    container_id = f"phoenix-container-{int(time.time())}"
    display(HTML(f"""
        <div id="{container_id}" class="phoenix-launcher-output" style="height: 95vh; border: 1px solid #444; border-radius: 8px; overflow: hidden;">
            <p style="color: #e8eaed; font-family: 'Noto Sans TC', sans-serif; padding: 20px;">
                ⚙️ 指揮官，正在初始化鳳凰之心駕駛艙...
            </p>
        </div>
    """))

    # --- 步驟 2: 將 Colab 表單參數設定為環境變數 ---
    # 這是將您的設定傳遞給後端的核心機制
    print("✅ 正在設定環境變數...")
    os.environ['LOG_DISPLAY_LINES'] = str(LOG_DISPLAY_LINES)
    os.environ['STATUS_REFRESH_INTERVAL'] = str(STATUS_REFRESH_INTERVAL)
    os.environ['ARCHIVE_FOLDER_NAME'] = str(ARCHIVE_FOLDER_NAME)
    os.environ['FASTAPI_PORT'] = str(FASTAPI_PORT)
    print(f"   - 日誌行數: {LOG_DISPLAY_LINES}")
    print(f"   - 刷新頻率: {STATUS_REFRESH_INTERVAL}s")
    print(f"   - 歸檔目錄: {ARCHIVE_FOLDER_NAME}")
    print(f"   - 服務埠號: {FASTAPI_PORT}")

    # --- 步驟 3: 驗證並進入專案目錄 ---
    project_path = Path("/content") / TARGET_FOLDER_NAME
    if not project_path.is_dir() or not (project_path / "main.py").exists():
        raise FileNotFoundError(f"指定的專案資料夾 '{project_path}' 不存在或缺少 'main.py' 核心檔案。")

    print(f"📂 已成功定位專案目錄: {project_path}")
    os.chdir(project_path)

    # --- 步驟 4: 安裝/驗證專案依賴 (阻塞式) ---
    print("\n🚀 正在配置專案環境，請稍候...")
    # 執行依賴安裝腳本，並等待其完成
    install_result = subprocess.run(
        ["python3", "uv_manager.py"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if install_result.returncode != 0:
        print("❌ 依賴配置失敗，終止作戰。")
        print("--- STDERR ---")
        print(install_result.stderr)
        raise RuntimeError("依賴安裝失敗。")

    print("✅ 專案環境配置成功。")
    print(install_result.stdout)

    # --- 步驟 5: 在背景啟動 FastAPI 伺服器 ---
    print("\n🔥 正在點燃後端引擎...")
    server_process = subprocess.Popen(
        ["python3", "run.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True, encoding='utf-8'
    )
    print(f"   - 後端伺服器程序已啟動 (PID: {server_process.pid})。")

    # --- 步驟 6: 等待伺服器就緒並嵌入駕駛艙 ---
    print("📡 正在等待伺服器響應...")
    time.sleep(10) # 給予伺服器足夠的啟動時間

    print(f"🌍 正在將駕駛艙嵌入至容器 (ID: {container_id})...")
    # 使用 JavaScript 將 iframe 嵌入到我們之前建立的 div 中
    js_code = f"""
        const container = document.getElementById('{container_id}');
        if (container) {{
            container.innerHTML = ''; // 清空 "正在初始化" 的訊息
            const iframe = document.createElement('iframe');
            iframe.src = `https://localhost:{FASTAPI_PORT}`;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            container.appendChild(iframe);
        }}
    """
    display(Javascript(js_code))
    print("\n✅ 鳳凰之心駕駛艙已上線！")
    print("ℹ️ 要停止所有服務，請點擊此儲存格左側的「中斷執行」(■) 按鈕。")

    # --- 步驟 7: 監控後端日誌並保持 Colab 活躍 ---
    # 為了方便除錯，我們可以選擇性地打印後端日誌
    for line in iter(server_process.stdout.readline, ''):
        if "Uvicorn running on" in line: # 捕捉關鍵啟動訊息
            print(f"   - [後端引擎]: {line.strip()}")

    server_process.wait() # 等待進程結束

except KeyboardInterrupt:
    print("\n\n🛑 [偵測到使用者手動中斷請求...]")
except Exception as e:
    print(f"\n\n💥 作戰流程發生未預期的嚴重錯誤: {e}", file=sys.stderr)
finally:
    # --- 終端清理程序 ---
    if server_process and server_process.poll() is None:
        print(" shutting down the backend server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("✅ 後端伺服器已成功終止。")
        except subprocess.TimeoutExpired:
            print("⚠️ 伺服器未能溫和終止，將強制結束。")
            server_process.kill()

    print("\n--- 系統已安全關閉 ---")
