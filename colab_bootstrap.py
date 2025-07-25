import os
import subprocess
import sys
import time
from IPython.display import display, HTML

def main(
    LOG_DISPLAY_LINES: int = 100,
    STATUS_REFRESH_INTERVAL: float = 0.5,
    TARGET_FOLDER_NAME: str = "WEB",
    ARCHIVE_FOLDER_NAME: str = "作戰日誌歸檔",
    FASTAPI_PORT: int = 8000,
):
    """
    Colab 引導腳本，設定環境、啟動後端並顯示儀表板。
    """
    print("--- 鳳凰之心 v14.0 參數化啟動程序 ---")

    # 1. 設定環境變數
    print("步驟 1/4: 設定環境變數...")
    os.environ['LOG_DISPLAY_LINES'] = str(LOG_DISPLAY_LINES)
    os.environ['STATUS_REFRESH_INTERVAL'] = str(STATUS_REFRESH_INTERVAL)
    os.environ['TARGET_FOLDER_NAME'] = TARGET_FOLDER_NAME
    os.environ['ARCHIVE_FOLDER_NAME'] = ARCHIVE_FOLDER_NAME
    os.environ['FASTAPI_PORT'] = str(FASTAPI_PORT)
    print(f"  - 日誌顯示行數: {LOG_DISPLAY_LINES}")
    print(f"  - 狀態刷新間隔: {STATUS_REFRESH_INTERVAL}s")
    print(f"  - 目標資料夾: {TARGET_FOLDER_NAME}")
    print(f"  - 歸檔資料夾: {ARCHIVE_FOLDER_NAME}")
    print(f"  - FastAPI 埠號: {FASTAPI_PORT}")

    # 2. 切換工作目錄 (如果需要)
    # 在這個專案結構中，我們假設腳本在根目錄執行，所以不需要切換
    print("\n步驟 2/4: 確認工作目錄...")
    print(f"  - 目前工作目錄: {os.getcwd()}")


    # 3. 啟動後端伺服器
    print("\n步驟 3/4: 在背景啟動 FastAPI 伺服器...")
    # 使用 sys.executable 確保我們用的是當前 Colab 環境的 Python 直譯器
    command = [
        sys.executable, "-m", "uvicorn",
        "main:app",
        "--host", "0.0.0.0",
        "--port", str(FASTAPI_PORT)
    ]

    try:
        server_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print("  - 伺服器程序已啟動。PID:", server_process.pid)
        # 等待一小段時間確保伺服器已啟動
        time.sleep(5)
    except Exception as e:
        print(f"  - 錯誤：無法啟動伺服器: {e}")
        return

    # 4. 顯示儀表板
    print("\n步驟 4/4: 渲染前端儀表板...")

    # 使用 IFrame 顯示儀表板
    iframe_html = f"""
    <iframe src="http://localhost:{FASTAPI_PORT}" width="100%" height="600" frameborder="0"></iframe>
    """
    display(HTML(iframe_html))
    print("--- 啟動程序完畢 ---")

    # 讓 Colab cell 保持運行以顯示日誌
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n--- 收到中斷訊號，正在關閉伺服器... ---")
        server_process.terminate()
        server_process.wait()
        print("--- 伺服器已關閉。 ---")
