# colab_main.py (融合版)

import subprocess
import time
import threading
from pathlib import Path
from integrated_platform.src.log_manager import LogManager
from integrated_platform.src.display_manager import DisplayManager
from google.colab import output as colab_output
from IPython.display import display, HTML

# --- 核心設定 ---
LOG_DB_PATH = Path("logs.sqlite")
PROJECT_ROOT = Path("/app/integrated_platform")
HOST = "0.0.0.0"
PORT = 8000

# 全局日誌管理器，以便在 create_public_portal 中使用
log_manager = LogManager(LOG_DB_PATH)

def create_public_portal(port=PORT, retries=5, delay=3):
    """
    建立一個從 Colab 連接到後端服務的公開服務入口。

    Args:
        port (int): 後端服務運行的埠號。
        retries (int): 失敗時的重試次數。
        delay (int): 每次重試之間的延遲秒數。
    """
    log_manager.log("INFO", "奉命建立服務入口...")

    button_html_template = """
    <a href="{url}" target="_blank" style="
        background-color: #4CAF50; /* 綠色背景 */
        border: none;
        color: white; /* 白色文字 */
        padding: 15px 32px;
        text-align: center;
        text-decoration: none;
        display: inline-block;
        font-size: 16px;
        margin: 4px 2px;
        cursor: pointer;
        border-radius: 12px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition-duration: 0.4s;
    ">
        🚀 點此開啟「鳳凰轉錄儀」指揮中心
    </a>
    """

    for attempt in range(retries):
        try:
            # 讓 Colab 將核心埠號作為一個窗口提供服務
            colab_output.serve_kernel_port_as_window(port, path='/')
            log_manager.log("INFO", f"Colab 服務窗口已在埠 {port} 上設定。")

            # 構造公開 URL
            public_url = colab_output.eval_js(f"google.colab.kernel.proxyPort({port})")

            # 顯示漂亮的按鈕
            display(HTML(button_html_template.format(url=public_url)))

            log_manager.log("SUCCESS", f"服務入口已建立！作戰指揮中心位於: {public_url}")
            return
        except Exception as e:
            log_manager.log("WARNING", f"建立服務入口嘗試 #{attempt + 1} 失敗: {e}")
            if attempt < retries - 1:
                log_manager.log("INFO", f"將在 {delay} 秒後重試...")
                time.sleep(delay)

    log_manager.log("CRITICAL", "所有建立公開服務入口的嘗試均告失敗。請檢查 Colab 環境與後端服務狀態。")


def stream_logs(process, log_manager_instance):
    """在一個單獨的執行緒中，讀取子進程的輸出並寫入日誌。"""
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            log_manager_instance.log("UVICORN", line.strip())
        process.stdout.close()

def main():
    """
    Colab Notebook 的主執行流程。
    """
    # 1. 初始化顯示管理器 (日誌管理器已在全域初始化)
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

        # 4. 等待伺服器啟動後，建立公開服務入口
        log_manager.log("INFO", "等待後端伺服器穩定...")
        time.sleep(5) # 給予 Uvicorn 足夠的啟動時間
        create_public_portal()

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
