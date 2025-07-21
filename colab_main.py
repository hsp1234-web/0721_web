# colab_main.py

import subprocess
import time
from pathlib import Path
from integrated_platform.src.log_manager import LogManager
from integrated_platform.src.display_manager import DisplayManager

# --- 核心設定 ---
LOG_DB_PATH = Path("logs.sqlite")

def main():
    """
    Colab Notebook 的主執行流程。
    """
    # 1. 初始化日誌管理器
    log_manager = LogManager(LOG_DB_PATH)

    # 2. 提前喚醒「畫家」
    display_manager = DisplayManager(LOG_DB_PATH)
    display_manager.start()

    log_manager.log("INFO", "顯示管理器已在背景啟動。")

    # 3. 執行耗時的後端部署腳本
    log_manager.log("INFO", "正在執行後端部署腳本 (run.sh)...")

    try:
        # 使用 subprocess 執行，並將輸出導向日誌
        process = subprocess.Popen(
            ["bash", "run.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )

        # 即時讀取腳本輸出並寫入日誌
        for line in iter(process.stdout.readline, ''):
            log_manager.log("SHELL", line.strip())

        process.wait()

        if process.returncode == 0:
            log_manager.log("INFO", "後端部署腳本執行成功。")
        else:
            log_manager.log("ERROR", f"後端部署腳本執行失敗，返回碼: {process.returncode}")

    except Exception as e:
        log_manager.log("CRITICAL", f"執行 run.sh 時發生嚴重錯誤: {e}")


    # 4. 模擬一些前端操作
    log_manager.log("INFO", "正在模擬前端 API 請求...")
    time.sleep(2)
    log_manager.log("DEBUG", "請求 /api/apps...")
    time.sleep(1)
    log_manager.log("INFO", "成功獲取應用列表。")
    time.sleep(2)
    log_manager.log("INFO", "正在上傳檔案到 /api/transcribe/upload...")
    time.sleep(1)
    log_manager.log("INFO", "檔案上傳和轉寫完成。")


    # 5. 任務結束，停止顯示管理器
    log_manager.log("INFO", "所有任務已完成，正在關閉顯示管理器。")
    time.sleep(5) # 等待最後的日誌被擷取
    display_manager.stop()

if __name__ == "__main__":
    # 為了能在本地測試，我們假設有一個 `__main__`
    # 在 Colab 中，您會直接呼叫 main()
    main()
