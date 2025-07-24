# -*- coding: utf-8 -*-
# 整合型應用平台 Colab 啟動器
# 版本: 6.0.0 (雙區域儀表板)
# 此腳本使用 google.colab.html 建立一個包含日誌和應用程式的雙區域儀表板。

import sys
import threading
import time
import queue
import logging
from pathlib import Path
from IPython.display import display, HTML
from google.colab import output
from google.colab.kernel import proxy_kernel_driver

# --- 全域配置 (可由 Colab Notebook 修改) ---
PORT = 8000
HOST = "127.0.0.1"
LOG_DISPLAY_LINES = 100
STATUS_REFRESH_INTERVAL = 1.0
APP_VERSION = "v6.0.0"

# --- 內部配置 ---
LOG_QUEUE = queue.Queue()
STOP_EVENT = threading.Event()
DASHBOARD_TEMPLATE_PATH = Path("static/colab_dashboard.html")

# --- 日誌系統 ---
class QueueHandler(logging.Handler):
    """將日誌記錄發送到佇列的處理程序。"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        self.log_queue.put(self.format(record))

def setup_logging():
    """設定全域日誌記錄器，將日誌同時輸出到控制台和佇列。"""
    log_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # 主記錄器
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # 控制台輸出
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(log_formatter)
    logger.addHandler(stream_handler)

    # 佇列輸出
    queue_handler = QueueHandler(LOG_QUEUE)
    queue_handler.setFormatter(log_formatter)
    logger.addHandler(queue_handler)

# --- 儀表板與日誌更新 ---
def log_updater_thread():
    """從佇列中獲取日誌並使用 JS 更新前端的執行緒。"""
    logs = []
    while not STOP_EVENT.is_set():
        try:
            log_record = LOG_QUEUE.get(timeout=1)
            logs.append(log_record)

            # 保持日誌列表只顯示指定的行數
            if len(logs) > LOG_DISPLAY_LINES:
                logs.pop(0)

            # 清理日誌文字中的特殊字元，以安全地傳遞給 JS
            log_text_for_js = "\\n".join(logs).replace("'", "\\'").replace('"', '\\"')

            # 使用 eval_js 來呼叫一個 JS 函式更新日誌區域
            output.eval_js(f"""
                (function() {{
                    const logDisplay = document.getElementById('log-display');
                    if (logDisplay) {{
                        logDisplay.textContent = '{log_text_for_js}';
                        logDisplay.scrollTop = logDisplay.scrollHeight;
                    }}
                }})();
            """)
        except queue.Empty:
            continue
        except Exception as e:
            # 在主控台中打印更新執行緒的錯誤
            print(f"Log updater thread error: {e}", file=sys.stderr)

def display_dashboard(app_url: str):
    """讀取 HTML 模板，注入 URL，並顯示儀表板。"""
    if not DASHBOARD_TEMPLATE_PATH.exists():
        logging.error(f"找不到儀表板模板檔案: {DASHBOARD_TEMPLATE_PATH}")
        return

    template = DASHBOARD_TEMPLATE_PATH.read_text(encoding='utf-8')
    html_content = template.replace("{{APP_URL}}", app_url)

    # 清除之前的任何輸出並顯示新的 HTML 儀表板
    output.clear()
    display(HTML(html_content))
    logging.info("雙區域作戰儀表板已成功渲染。")

# --- 主執行流程 ---
def main():
    """Colab 環境的主執行流程。"""
    setup_logging()

    _print_header("階段一：啟動主應用程式")
    try:
        import run
        # 將 PORT 傳遞給 run 模組
        run.PORT = PORT
        app_thread = threading.Thread(target=run.main, daemon=True)
        app_thread.start()
        logging.info(f"主應用程式執行緒已在背景啟動，目標埠號 {PORT}。")
    except Exception as e:
        logging.critical(f"啟動 'run.py' 時發生致命錯誤: {e}", exc_info=True)
        return

    _print_header("階段二：建立 Colab 內部代理並渲染儀表板")
    try:
        # 獲取 Colab 為我們服務的代理 URL
        app_url = proxy_kernel_driver.get_external_url(PORT)
        logging.info(f"成功獲取應用程式代理 URL: {app_url}")

        # 顯示儀表板
        display_dashboard(app_url)

        # 啟動日誌更新執行緒
        log_thread = threading.Thread(target=log_updater_thread, daemon=True)
        log_thread.start()
        logging.info("日誌更新執行緒已啟動。")

    except Exception as e:
        logging.critical(f"建立儀表板時發生錯誤: {e}", exc_info=True)
        return

    # 保持主執行緒活躍，直到被使用者中斷
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("偵測到手動中斷，正在關閉服務...")
        STOP_EVENT.set()

def _print_header(title: str):
    """使用 logging 印出帶有風格的標頭。"""
    logging.info("="*80)
    logging.info(f"🚀 {title}")
    logging.info("="*80)

if __name__ == "__main__":
    main()
else:
    # 允許 'import colab_run' 直接執行
    # Colab Notebook 會先設定好 PORT 等變數，然後才呼叫 main()
    pass
