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

import os
import sys
import subprocess
import time
import logging
from pathlib import Path
from datetime import datetime
import pytz
from IPython.display import display, HTML, Javascript

# ==============================================================================
# SECTION 1: 全域變數與日誌設定
# ==============================================================================
server_process = None
log_buffer = []

def setup_colab_logging(archive_dir, log_filename):
    """設定一個專用於 Colab 啟動腳本的日誌記錄器。"""
    log_path = Path(archive_dir) / log_filename
    log_path.parent.mkdir(exist_ok=True)

    # 清除此 logger 可能存在的舊 handlers
    logger = logging.getLogger("colab_launcher")
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging.INFO)

    # 檔案 handler
    fh = logging.FileHandler(log_path, encoding='utf-8')
    fh.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 控制台 handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setLevel(logging.INFO)
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger, str(log_path)

# 產生唯一的日誌檔名
tz = pytz.timezone('Asia/Taipei')
timestamp = datetime.now(tz).strftime('%Y-%m-%dT%H-%M-%S')
colab_log_filename = f"Colab啟動日誌_{timestamp}.txt"

# 在腳本開始時就設定日誌
colab_logger, colab_log_path = setup_colab_logging(ARCHIVE_FOLDER_NAME, colab_log_filename)

# ==============================================================================
# SECTION 2: 核心啟動流程
# ==============================================================================
try:
    colab_logger.info("="*50)
    colab_logger.info("💎 鳳凰之心整合式指揮中心 v14.0 - 啟動程序開始")
    colab_logger.info("="*50)

    # --- 步驟 1: 清理並準備顯示區域 ---
    colab_logger.info("步驟 1/7: 清理 Colab 輸出區域...")
    display(Javascript("document.querySelectorAll('.phoenix-launcher-output').forEach(el => el.remove());"))
    time.sleep(0.2)

    container_id = f"phoenix-container-{int(time.time())}"
    display(HTML(f"""
        <div id="{container_id}" class="phoenix-launcher-output" style="height: 95vh; border: 1px solid #444; border-radius: 8px; overflow: hidden;">
            <p style="color: #e8eaed; font-family: 'Noto Sans TC', sans-serif; padding: 20px;">
                ⚙️ 指揮官，正在初始化鳳凰之心駕駛艙...
            </p>
        </div>
    """))
    colab_logger.info(f"   - 成功建立顯示容器 (ID: {container_id})")

    # --- 步驟 2: 設定環境變數 ---
    colab_logger.info("步驟 2/7: 設定環境變數...")
    os.environ['LOG_DISPLAY_LINES'] = str(LOG_DISPLAY_LINES)
    os.environ['STATUS_REFRESH_INTERVAL'] = str(STATUS_REFRESH_INTERVAL)
    os.environ['ARCHIVE_FOLDER_NAME'] = str(ARCHIVE_FOLDER_NAME)
    os.environ['FASTAPI_PORT'] = str(FASTAPI_PORT)
    colab_logger.info(f"   - 日誌行數: {LOG_DISPLAY_LINES}")
    colab_logger.info(f"   - 刷新頻率: {STATUS_REFRESH_INTERVAL}s")
    colab_logger.info(f"   - 歸檔目錄: {ARCHIVE_FOLDER_NAME}")
    colab_logger.info(f"   - 服務埠號: {FASTAPI_PORT}")

    # --- 步驟 3: 驗證並進入專案目錄 ---
    colab_logger.info("步驟 3/7: 驗證並進入專案目錄...")
    # 注意：在Colab中，所有內容通常都在 /content/ 下
    # 我們假設這個 notebook 和 TARGET_FOLDER_NAME 都在 /content/
    base_path = Path("/content")
    project_path = base_path / TARGET_FOLDER_NAME

    if not project_path.is_dir() or not (project_path / "main.py").exists():
        raise FileNotFoundError(f"指定的專案資料夾 '{project_path}' 不存在或缺少 'main.py' 核心檔案。")

    os.chdir(project_path)
    colab_logger.info(f"   - 已成功切換至專案目錄: {os.getcwd()}")

    # --- 步驟 4: 安裝/驗證專案依賴 ---
    colab_logger.info("步驟 4/7: 配置專案環境...")
    install_result = subprocess.run(
        ["python3", "uv_manager.py"],
        capture_output=True, text=True, encoding='utf-8'
    )
    if install_result.returncode != 0:
        colab_logger.error("❌ 依賴配置失敗，終止作戰。")
        colab_logger.error(f"--- STDERR ---\n{install_result.stderr}")
        raise RuntimeError("依賴安裝失敗。")

    colab_logger.info("   - ✅ 專案環境配置成功。")
    colab_logger.info(f"--- uv_manager.py STDOUT ---\n{install_result.stdout}")

    # --- 步驟 5: 啟動 FastAPI 伺服器 ---
    colab_logger.info("步驟 5/7: 點燃後端引擎...")
    # 這裡我們傳遞日誌檔名給後端
    server_process = subprocess.Popen(
        ["python3", "run.py", "--log-file", colab_log_filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True, encoding='utf-8'
    )
    colab_logger.info(f"   - 後端伺服器程序已啟動 (PID: {server_process.pid})。")

    # --- 步驟 6: 等待伺服器就緒並嵌入駕駛艙 ---
    colab_logger.info("步驟 6/7: 等待伺服器響應並嵌入駕駛艙...")
    time.sleep(10)

    js_code = f"""
        const container = document.getElementById('{container_id}');
        if (container) {{
            container.innerHTML = '';
            const iframe = document.createElement('iframe');
            iframe.src = `https://localhost:{FASTAPI_PORT}`;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = 'none';
            container.appendChild(iframe);
        }}
    """
    display(Javascript(js_code))
    colab_logger.info("   - ✅ 鳳凰之心駕駛艙已上線！")

    # --- 步驟 7: 監控後端日誌 ---
    colab_logger.info("步驟 7/7: 進入後端日誌監控模式...")
    print("\n--- 後端日誌 (僅顯示部分關鍵訊息) ---")
    for line in iter(server_process.stdout.readline, ''):
        if "Uvicorn running on" in line:
            print(f"   - [後端引擎]: {line.strip()}")
            colab_logger.info(f"[後端引擎]: {line.strip()}")

    server_process.wait()

except KeyboardInterrupt:
    colab_logger.warning("\n🛑 [偵測到使用者手動中斷請求...]")
except Exception as e:
    colab_logger.error(f"\n💥 作戰流程發生未預期的嚴重錯誤: {e}", exc_info=True)
finally:
    colab_logger.info("="*50)
    colab_logger.info("Σ 終端清理程序開始")
    colab_logger.info("="*50)
    if server_process and server_process.poll() is None:
        colab_logger.info("   - 正在關閉後端伺服器...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            colab_logger.info("   - ✅ 後端伺服器已成功終止。")
        except subprocess.TimeoutExpired:
            colab_logger.warning("   - ⚠️ 伺服器未能溫和終止，將強制結束。")
            server_process.kill()

    colab_logger.info(f"詳細執行日誌已儲存至: {colab_log_path}")
    colab_logger.info("--- 系統已安全關閉 ---")

    # 關閉 logger 的 file handler，確保所有內容都寫入檔案
    for handler in colab_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            handler.close()
            colab_logger.removeHandler(handler)
