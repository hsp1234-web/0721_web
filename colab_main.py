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

def create_public_portal(port=8000, retries=5, delay=3):
    """
    建立一個從 Colab 連接到後端服務的公開門戶。

    這個函式會嘗試使用 `google.colab.output.serve_kernel_port_as_window`
    來建立一個可公開存取的 URL。如果失敗，它會進行有限次數的重試。

    Args:
        port (int): 要公開的本地埠號。
        retries (int): 失敗時的最大重試次數。
        delay (int): 每次重試之間的延遲秒數。
    """
    log_manager.log("INFO", "奉命建立服務入口...")

    button_html_template = """
    <a href="{url}" target="_blank" style="
        display: inline-block;
        padding: 12px 24px;
        background-color: #4CAF50; /* Green */
        color: white;
        text-align: center;
        text-decoration: none;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        box-shadow: 0 4px 8px 0 rgba(0,0,0,0.2);
        transition: 0.3s;
    ">
        🚀 點此開啟「鳳凰轉錄儀」指揮中心
    </a>
    """

    for attempt in range(retries):
        try:
            # 呼叫 Colab API 來建立並開啟一個代理視窗
            colab_output.serve_kernel_port_as_window(port, path="/")

            # 在 Colab 中，serve_kernel_port_as_window 會自動處理 URL
            # 我們這裡假設它成功了，並顯示一個按鈕
            # 注意：在本地環境中，這行會拋出異常
            public_url = f"https://localhost:{port}" # 僅為示意

            # 顯示漂亮的 HTML 按鈕
            display(HTML(button_html_template.format(url=public_url)))

            log_manager.log("SUCCESS", f"服務入口已建立！請點擊上方按鈕開啟指揮中心。")
            return
        except Exception as e:
            log_manager.log("WARNING", f"建立服務入口嘗試 #{attempt + 1} 失敗: {e}")
            if attempt < retries - 1:
                log_manager.log("INFO", f"將在 {delay} 秒後重試...")
                time.sleep(delay)

    log_manager.log("CRITICAL", "所有建立公開服務入口的嘗試均失敗。請檢查 Colab 環境設定。")


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

    # 5. 任務結束，提示使用者
    log_manager.log("INFO", "主要作戰流程已執行完畢。顯示管理器將會繼續運行以接收後續日誌。")
    # 我們不再自動停止，讓用戶可以持續看到日誌
    # time.sleep(5)
    # display_manager.stop()

if __name__ == "__main__":
    # 為了能在本地測試，我們假設有一個 `__main__`
    # 在 Colab 中，您會直接呼叫 main()
    main()
