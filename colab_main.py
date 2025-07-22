# colab_main.py

import subprocess
import time
from pathlib import Path
from integrated_platform.src.log_manager import LogManager
from integrated_platform.src.display_manager import DisplayManager
from google.colab import output as colab_output
from IPython.display import display, HTML

# --- 核心設定 ---
LOG_DB_PATH = Path("logs.sqlite")
log_manager = LogManager(LOG_DB_PATH)

def create_public_portal(port=8000):
    """
    使用 serve_kernel_port_as_iframe 建立一個內嵌的服務入口。
    """
    log_manager.log("INFO", f"奉命建立服務入口...")
    try:
        colab_output.serve_kernel_port_as_iframe(port, path='/', height='800')
        log_manager.log("SUCCESS", "服務入口已成功建立！")
    except Exception as e:
        log_manager.log("CRITICAL", f"建立 iframe 服務入口時發生致命錯誤: {e}")


def main():
    """
    Colab Notebook 的主執行流程。
    """
    display_thread = None
    # 引入 STOP_EVENT 以協調關閉
    STOP_EVENT = threading.Event()

    try:
        # 1. 初始化並啟動 DisplayManager
        # 我們將 stop_event 傳遞給它
        display_manager = DisplayManager(LOG_DB_PATH, STOP_EVENT)
        display_manager.start()
        display_thread = display_manager.thread # 引用執行緒以供稍後 join
        log_manager.log("INFO", "顯示管理器已在背景啟動。")

        # 2. 執行後端部署腳本
        log_manager.log("INFO", "正在執行後端部署腳本 (run.sh)...")
        run_success = False
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

        # 3. 如果成功，建立服務入口
        if run_success:
            create_public_portal()

        # 4. 讓腳本保持運行，直到被手動中斷
        log_manager.log("INFO", "主要作戰流程已執行完畢。請手動中斷儲存格以結束任務。")
        while not STOP_EVENT.is_set():
            time.sleep(1)

    except KeyboardInterrupt:
        log_manager.log("WARNING", "偵測到手動中斷指令！正在準備優雅關閉...")

    except Exception as e:
        log_manager.log("CRITICAL", f"主流程發生未預期錯誤: {e}")

    finally:
        log_manager.log("INFO", "正在執行終端清理程序...")
        STOP_EVENT.set()

        # 確保 display_thread 存在且不是當前執行緒
        if display_thread and display_thread.is_alive():
            display_thread.join(timeout=2) # 等待顯示執行緒結束
            log_manager.log("INFO", "顯示管理器已關閉。")

        # 這裡可以加上日誌歸檔的邏輯
        # from integrated_platform.src.archiver import archive_final_log
        # archive_final_log(LOG_DB_PATH)

        print("\n[部署流程已結束，所有服務已安全關閉。]")

if __name__ == "__main__":
    # 為了能在本地測試，我們假設有一個 `__main__`
    # 在 Colab 中，您會直接呼叫 main()
    main()
