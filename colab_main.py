# colab_main.py

import subprocess
import time
from pathlib import Path
from integrated_platform.src.log_manager import LogManager
from integrated_platform.src.display_manager import DisplayManager
from google.colab import output as colab_output

# --- 核心設定 ---
LOG_DB_PATH = Path("logs.sqlite")
log_manager = LogManager(LOG_DB_PATH)

def create_public_portal(port=8000, height=800):
    """
    使用官方推薦的 iframe 方式，在 Colab 輸出儲存格中直接建立一個穩定的服務視窗。

    Args:
        port (int): FastAPI 服務運行的埠號。
        height (int): 內嵌視窗的高度。
    """
    log_manager.log("INFO", "奉命建立服務入口...")
    try:
        # 直接呼叫 Colab 官方推薦的 serve_kernel_port_as_iframe 函式
        colab_output.serve_kernel_port_as_iframe(port, height=height)
        log_manager.log("SUCCESS", "服務入口已在下方儲存格建立！您可以直接開始操作。")
    except Exception as e:
        log_manager.log("CRITICAL", f"建立服務入口時發生嚴重錯誤: {e}")


def main():
    """
    Colab Notebook 的主執行流程。
    """
    # 1. 初始化日誌管理器 (已移至全域)

    # 2. 提前喚醒「畫家」
    display_manager = DisplayManager(LOG_DB_PATH)
    display_manager.start()

    log_manager.log("INFO", "顯示管理器已在背景啟動。")

    # 3. 執行耗時的後端部署腳本
    log_manager.log("INFO", "正在執行後端部署腳本 (run.sh)...")

    run_success = False
    try:
        process = subprocess.Popen(
            ["bash", "run.sh"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )

        for line in iter(process.stdout.readline, ''):
            log_manager.log("SHELL", line.strip())

        process.wait()

        if process.returncode == 0:
            log_manager.log("SUCCESS", "後端部署腳本執行完畢。")
            run_success = True
        else:
            log_manager.log("ERROR", f"後端部署腳本執行失敗，返回碼: {process.returncode}")

    except Exception as e:
        log_manager.log("CRITICAL", f"執行 run.sh 時發生嚴重錯誤: {e}")

    # 4. 如果後端部署成功，則建立公開服務入口
    if run_success:
        create_public_portal()

    # 5. 進入持續等待狀態，保持日誌畫面存活
    log_manager.log("INFO", "主要作戰流程已執行完畢。系統現在進入持續監控模式。")
    log_manager.log("INFO", "您可以隨時在 Colab 中點擊「中斷執行」按鈕來終止所有服務。")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        log_manager.log("INFO", "偵測到手動中斷指令，開始執行關機程序...")
        display_manager.stop()
        log_manager.log("INFO", "所有服務已安全關閉。")


if __name__ == "__main__":
    # 為了能在本地測試，我們假設有一個 `__main__`
    # 在 Colab 中，您會直接呼叫 main()
    main()
