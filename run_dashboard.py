#@title 💎 鳳凰之心整合式指揮中心 v14.1 (即時加載版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **核心參數與路徑配置**
#@markdown > **在啟動前，確認所有設定。點擊「執行」後，將立即顯示安裝日誌。**
#@markdown ---
LOG_DISPLAY_LINES = 100 #@param {type:"integer"}
STATUS_REFRESH_INTERVAL = 0.5 #@param {type:"number"}
TARGET_FOLDER_NAME = "WEB" #@param {type:"string"}
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **主應用伺服器埠號 (MAIN_APP_PORT)**
MAIN_APP_PORT = 8000 #@param {type:"integer"}
#@markdown **引導伺服器埠號 (BOOTSTRAP_PORT)**
#@markdown > **這個埠號用於直播安裝過程，通常不需要修改。**
BOOTSTRAP_PORT = 8001 #@param {type:"integer"}
#@markdown ---

import os
import sys
import subprocess
import time
import logging
import asyncio
import threading
from pathlib import Path
from datetime import datetime
import pytz
from IPython.display import display, HTML, Javascript

# 確保能從根目錄導入模組
if Path.cwd().name == TARGET_FOLDER_NAME:
    os.chdir("..")
sys.path.insert(0, str(Path.cwd()))

from core.bootstrap_server import bootstrap_app, bootstrap_manager, start_bootstrap_server

# ==============================================================================
# SECTION 1: 日誌與多執行緒設定
# ==============================================================================
server_process = None
bootstrap_server_instance = None

def setup_launcher_logging(archive_dir, log_filename):
    log_path = Path(archive_dir) / log_filename
    log_path.parent.mkdir(exist_ok=True)
    logger = logging.getLogger("colab_launcher")
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.INFO)
    fh = logging.FileHandler(log_path, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    logger.addHandler(sh)
    return logger, str(log_path)

tz = pytz.timezone('Asia/Taipei')
timestamp = datetime.now(tz).strftime('%Y-%m-%dT%H-%M-%S')
launcher_log_filename = f"啟動器日誌_{timestamp}.txt"
launcher_logger, launcher_log_path = setup_launcher_logging(ARCHIVE_FOLDER_NAME, launcher_log_filename)

def stream_subprocess_output(pipe, event_type):
    """讀取子程序的輸出，並透過 WebSocket 廣播。"""
    try:
        for line in iter(pipe.readline, ''):
            asyncio.run(bootstrap_manager.broadcast({
                "event_type": event_type,
                "payload": line.strip()
            }))
        pipe.close()
    except Exception as e:
        launcher_logger.error(f"串流日誌時發生錯誤: {e}", exc_info=True)

# ==============================================================================
# SECTION 2: 核心啟動流程
# ==============================================================================
async def main():
    global server_process, bootstrap_server_instance
    launcher_logger.info("="*50)
    launcher_logger.info("💎 鳳凰之心 v14.1 - 分段加載程序開始")
    launcher_logger.info("="*50)

    # === 階段一：立即啟動引導伺服器並渲染前端 ===
    launcher_logger.info("階段 1/4: 啟動引導伺服器...")
    bootstrap_server_instance, _ = await start_bootstrap_server(port=BOOTSTRAP_PORT)
    launcher_logger.info(f"   - ✅ 引導伺服器已在背景執行於埠 {BOOTSTRAP_PORT}")

    container_id = f"phoenix-container-{int(time.time())}"
    display(HTML(f"""
        <div id="{container_id}" class="phoenix-launcher-output" style="height: 95vh;"></div>
    """))

    # 傳遞兩個 port 給前端
    js_code = f"""
        const container = document.getElementById('{container_id}');
        if (container) {{
            const iframe = document.createElement('iframe');
            iframe.src = `https://localhost:{MAIN_APP_PORT}?bootstrapPort={BOOTSTRAP_PORT}`;
            iframe.style.width = '100%';
            iframe.style.height = '100%';
            iframe.style.border = '1px solid #444';
            iframe.style.borderRadius = '8px';
            container.appendChild(iframe);
        }}
    """
    display(Javascript(js_code))
    launcher_logger.info("   - ✅ 前端 IFrame 已渲染，準備接收安裝日誌。")

    try:
        # === 階段二：串流安裝日誌 ===
        launcher_logger.info("階段 2/4: 執行並串流依賴安裝日誌...")
        os.environ['LOG_DISPLAY_LINES'] = str(LOG_DISPLAY_LINES)
        os.environ['STATUS_REFRESH_INTERVAL'] = str(STATUS_REFRESH_INTERVAL)
        os.environ['ARCHIVE_FOLDER_NAME'] = str(ARCHIVE_FOLDER_NAME)
        os.environ['FASTAPI_PORT'] = str(MAIN_APP_PORT) # 主應用使用 MAIN_APP_PORT

        project_path = Path("/content") / TARGET_FOLDER_NAME
        if not project_path.is_dir() or not (project_path / "main.py").exists():
            raise FileNotFoundError(f"指定的專案資料夾 '{project_path}' 不存在或缺少 'main.py'。")
        os.chdir(project_path)
        launcher_logger.info(f"   - 已切換至專案目錄: {os.getcwd()}")

        install_process = subprocess.Popen(
            ["python3", "uv_manager.py"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8'
        )

        # 在背景執行緒中處理輸出，避免阻塞
        threading.Thread(target=stream_subprocess_output, args=(install_process.stdout, "INSTALL_LOG"), daemon=True).start()
        threading.Thread(target=stream_subprocess_output, args=(install_process.stderr, "INSTALL_ERROR"), daemon=True).start()

        install_process.wait() # 等待安裝完成
        if install_process.returncode != 0:
            raise RuntimeError("依賴安裝失敗，請檢查日誌。")
        launcher_logger.info("   - ✅ 依賴安裝成功。")

        # === 階段三：過渡至主伺服器 ===
        launcher_logger.info("階段 3/4: 準備過渡至主應用伺服器...")
        await bootstrap_manager.broadcast({"event_type": "INSTALL_COMPLETE", "payload": {}})
        launcher_logger.info("   - 已發送安裝完成信號至前端。")

        await asyncio.sleep(1) # 給前端一點反應時間
        bootstrap_server_instance.should_exit = True
        await bootstrap_server_instance.shutdown()
        launcher_logger.info("   - ✅ 引導伺服器已關閉。")

        # === 階段四：啟動主伺服器 ===
        launcher_logger.info("階段 4/4: 啟動主應用伺服器...")
        server_process = subprocess.Popen(
            ["python3", "run.py", "--log-file", launcher_log_filename],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            text=True, encoding='utf-8'
        )
        launcher_logger.info(f"   - ✅ 主應用伺服器已啟動 (PID: {server_process.pid})。")

        # 保持 Colab 儲存格活躍
        while server_process.poll() is None:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        launcher_logger.warning("\n🛑 [偵測到使用者手動中斷請求...]")
    except Exception as e:
        launcher_logger.error(f"\n💥 作戰流程發生嚴重錯誤: {e}", exc_info=True)
        # 如果出錯，也通知前端
        await bootstrap_manager.broadcast({"event_type": "INSTALL_ERROR", "payload": f"啟動器錯誤: {e}"})
    finally:
        launcher_logger.info("="*50)
        launcher_logger.info("Σ 終端清理程序開始")
        launcher_logger.info("="*50)
        if bootstrap_server_instance and not bootstrap_server_instance.should_exit:
            bootstrap_server_instance.should_exit = True
            await bootstrap_server_instance.shutdown()
            launcher_logger.info("   - 引導伺服器已清理。")
        if server_process and server_process.poll() is None:
            server_process.terminate()
            launcher_logger.info("   - 主應用伺服器已終止。")

        launcher_logger.info(f"詳細啟動日誌已儲存至: {launcher_log_path}")
        launcher_logger.info("--- 系統已安全關閉 ---")
        logging.shutdown()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nColab 執行被強制中斷。")
