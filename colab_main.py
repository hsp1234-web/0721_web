# colab_main.py (融合版)

import subprocess
import time
import threading
from pathlib import Path
from integrated_platform.src.log_manager import LogManager
from integrated_platform.src.display_manager import DisplayManager
from google.colab import output as colab_output

# --- 核心設定 ---
LOG_DB_PATH = Path("logs.sqlite")
PROJECT_ROOT = Path("/app/integrated_platform")
HOST = "0.0.0.0"
PORT = 8000

def stream_logs(process, log_manager):
    """在一個單獨的執行緒中，讀取子進程的輸出並寫入日誌。"""
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            log_manager.log("UVICORN", line.strip())
        process.stdout.close()

def main():
    """
    Colab Notebook 的主執行流程。
    """
    # 1. 初始化日誌和顯示管理器
    log_manager = LogManager(LOG_DB_PATH)
    display_manager = DisplayManager(LOG_DB_PATH)
    display_manager.start()
    log_manager.log("INFO", "顯示管理器已在背景啟動。")

    server_process = None
    log_thread = None

    try:
        # 2. 準備並啟動 Uvicorn 伺服器
        log_manager.log("INFO", "正在準備啟動後端伺服器...")

        # 清理舊的 server.log
        server_log_path = PROJECT_ROOT.parent / "server.log"
        if server_log_path.exists():
            server_log_path.unlink()

        run_command = [
            "poetry", "run", "uvicorn",
            "src.main:app",
            "--host", HOST,
            "--port", str(PORT)
        ]

        server_process = subprocess.Popen(
            run_command,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1
        )

        log_manager.log("INFO", f"後端伺服器進程已啟動 (PID: {server_process.pid})。")

        # 3. 啟動日誌流執行緒
        log_thread = threading.Thread(target=stream_logs, args=(server_process, log_manager), daemon=True)
        log_thread.start()

        # 4. 獲取並顯示 Colab 代理網址
        log_manager.log("INFO", "正在向 Colab 請求代理網址...")
        time.sleep(5) # 等待 Uvicorn 完全啟動
        try:
            public_url = colab_output.eval_js(f"google.colab.kernel.proxyPort({PORT})")
            log_manager.log("SUCCESS", f"應用程式已就緒！點此訪問： {public_url}")
        except Exception as e:
            log_manager.log("WARNING", f"無法自動獲取 Colab 代理網址: {e}")
            log_manager.log("INFO", f"請手動檢查 Colab 的輸出或代理埠 {PORT}。")

        # 5. 保持主執行緒運行，直到使用者中斷
        log_manager.log("INFO", "作戰系統已上線！要停止所有服務，請中斷此儲存格的執行。")
        while server_process.poll() is None:
            time.sleep(1)

    except KeyboardInterrupt:
        log_manager.log("INFO", "偵測到使用者手動中斷請求...")
    except Exception as e:
        log_manager.log("CRITICAL", f"主流程發生嚴重錯誤: {e}")
    finally:
        log_manager.log("INFO", "正在關閉所有服務...")
        if server_process and server_process.poll() is None:
            log_manager.log("INFO", f"正在終止後端伺服器進程 (PID: {server_process.pid})...")
            server_process.terminate()
            try:
                server_process.wait(timeout=5)
                log_manager.log("SUCCESS", "後端伺服器已成功終止。")
            except subprocess.TimeoutExpired:
                log_manager.log("WARNING", "終止超時，強制終止...")
                server_process.kill()
                log_manager.log("SUCCESS", "後端伺服器已被強制終止。")

        if log_thread and log_thread.is_alive():
            log_thread.join(timeout=2)

        log_manager.log("INFO", "所有任務已完成，正在關閉顯示管理器。")
        time.sleep(2) # 等待最後的日誌被擷取
        display_manager.stop()


if __name__ == "__main__":
    main()
