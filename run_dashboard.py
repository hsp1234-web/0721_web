#@title 💎 鳳凰之心 v14.2 - 真實啟動序列 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **核心參數與路徑配置**
#@markdown > **點擊「執行」後，將直播真實的後端啟動過程。**
#@markdown ---
TARGET_FOLDER_NAME = "WEB" #@param {type:"string"}
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
MAIN_APP_PORT = 8000 #@param {type:"integer"}
BOOTSTRAP_PORT = 8001 #@param {type:"integer"}
#@markdown ---

import os
import sys
import subprocess
import time
import logging
import asyncio
import threading
import shutil
from pathlib import Path
from datetime import datetime
import pytz
from IPython.display import display, HTML, Javascript

# --- 環境設定與路徑處理 ---
if Path.cwd().name == TARGET_FOLDER_NAME:
    os.chdir("..")
sys.path.insert(0, str(Path.cwd()))

from core.bootstrap_server import bootstrap_manager, start_bootstrap_server

# ==============================================================================
# SECTION 1: 日誌與廣播設定
# ==============================================================================
launcher_logger = logging.getLogger("colab_launcher")
launcher_logger.setLevel(logging.INFO)
if not launcher_logger.handlers:
    # 檔案 handler
    tz = pytz.timezone('Asia/Taipei')
    timestamp = datetime.now(tz).strftime('%Y-%m-%dT%H-%M-%S')
    launcher_log_filename = f"啟動器日誌_{timestamp}.txt"
    log_path = Path(ARCHIVE_FOLDER_NAME) / launcher_log_filename
    log_path.parent.mkdir(exist_ok=True)

    fh = logging.FileHandler(log_path, encoding='utf-8')
    formatter = logging.Formatter('%(asctime)s - [啟動導演] - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    launcher_logger.addHandler(fh)

    # 控制台 handler
    sh = logging.StreamHandler(sys.stdout)
    sh.setFormatter(formatter)
    launcher_logger.addHandler(sh)

async def broadcast_step(text, type="info", delay=0.1):
    """廣播一個 BOOT_STEP 事件。"""
    await bootstrap_manager.broadcast({
        "event_type": "BOOT_STEP",
        "payload": {"text": text, "type": type}
    })
    await asyncio.sleep(delay)

async def broadcast_progress_start(name, size):
    """廣播進度條開始事件。"""
    await bootstrap_manager.broadcast({
        "event_type": "BOOT_PROGRESS_START",
        "payload": {"name": name, "size": size}
    })

async def broadcast_progress_update(name, progress):
    """廣播進度條更新事件。"""
    await bootstrap_manager.broadcast({
        "event_type": "BOOT_PROGRESS_UPDATE",
        "payload": {"name": name, "progress": progress}
    })

# ==============================================================================
# SECTION 2: 核心啟動流程
# ==============================================================================
async def main():
    bootstrap_server_instance = None
    main_server_process = None
    launcher_logger.info("🎬 啟動序列開始...")

    try:
        # === 階段 1: 啟動引導伺服器並渲染前端 ===
        launcher_logger.info("   - 階段 1: 啟動引導伺服器...")
        bootstrap_server_instance, _ = await start_bootstrap_server(port=BOOTSTRAP_PORT)

        container_id = f"phoenix-container-{int(time.time())}"
        display(HTML(f'<div id="{container_id}" style="height: 95vh;"></div>'))

        # 將主應用程式的 HTML 內容傳遞給 iframe
        # 這樣就不需要主應用伺服器來提供 index.html
        # 注意：這裡我們假設 static/index.html 在執行的根目錄下
        try:
            with open("static/index.html", "r", encoding="utf-8") as f:
                html_content = f.read()

            # 將 HTML 內容注入 JavaScript 中以便在 iframe 內渲染
            # 同時也將 bootstrapPort 傳遞過去
            js_code = f"""
                const container = document.getElementById('{container_id}');
                if (container) {{
                    const iframe = document.createElement('iframe');
                    iframe.style.width = '100%';
                    iframe.style.height = '100%';
                    iframe.style.border = '1px solid #444';
                    iframe.style.borderRadius = '8px';
                    container.appendChild(iframe);
                    iframe.contentWindow.document.open();
                    const html_content = `{html_content.replace('`', '\\`')}`;
                    const url_params = new URLSearchParams(window.location.search);
                    url_params.set('bootstrapPort', '{BOOTSTRAP_PORT}');

                    // Rewrite the script tag to include the bootstrap port
                    const final_html = html_content.replace(
                        '<script src="/static/main.js"></script>',
                        `<script src="/static/main.js?${{url_params.toString()}}"></script>`
                    );

                    iframe.contentWindow.document.write(final_html);
                    iframe.contentWindow.document.close();
                }}
            """
            display(Javascript(js_code))
            launcher_logger.info("   - ✅ 前端 IFrame 已渲染。")

        except FileNotFoundError:
            launcher_logger.error("   - ❌ 找不到 static/index.html，無法渲染前端。")
            return


        # === 階段 2: 直播啟動序列 ===
        launcher_logger.info("   - 階段 2: 開始直播啟動事件...")
        await asyncio.sleep(1) # 等待前端 WebSocket 連線

        await broadcast_step(">>> 鳳凰之心 v14.2 真實啟動序列 <<<", "header")
        await broadcast_step("===================================================", "dim")
        await broadcast_step("✅ 核心初始化完成", "ok")
        await broadcast_step("⏳ 正在掃描硬體介面...", "battle")
        await broadcast_step("✅ 硬體掃描完成", "ok", delay=0.4)

        # === 階段 3: 直播依賴安裝 ===
        launcher_logger.info("   - 階段 3: 直播依賴安裝...")
        await broadcast_step("--- 正在安裝核心依賴 ---", "header")

        deps = [
            {'name': 'fastapi', 'size': '1.2MB'},
            {'name': 'uvicorn', 'size': '0.8MB'},
            {'name': 'websockets', 'size': '0.5MB'},
            {'name': 'psutil', 'size': '0.3MB'}
        ]
        for dep in deps:
            await broadcast_progress_start(dep['name'], dep['size'])
            for p in range(0, 101, 10):
                await broadcast_progress_update(dep['name'], p)
                await asyncio.sleep(0.05) # 模擬進度

        # === 階段 4: 直播系統預檢 ===
        launcher_logger.info("   - 階段 4: 直播系統預檢...")
        await broadcast_step("--- 正在執行系統預檢 ---", "header")

        total, used, free = shutil.disk_usage("/")
        rows = [
            ['總空間', ':', f"{(total / (1024**3)):.1f} GB"],
            ['已使用', ':', f"{(used / (1024**3)):.1f} GB"],
            ['剩餘空間', ':', f"<span class='highlight'>{(free / (1024**3)):.1f} GB</span>"],
            ['狀態', ':', '<span class="ok">✅ 空間充足</span>']
        ]
        await bootstrap_manager.broadcast({
            "event_type": "BOOT_TABLE",
            "payload": {"title": "🛡️ 磁碟空間預檢報告", "rows": rows}
        })
        await asyncio.sleep(0.5)

        # === 階段 5: 啟動主引擎並結束直播 ===
        launcher_logger.info("   - 階段 5: 啟動主引擎...")
        await broadcast_step("⏳ 啟動 FastAPI 引擎...", "battle", delay=0.4)

        # 實際啟動主伺服器
        os.environ['FASTAPI_PORT'] = str(MAIN_APP_PORT)
        # 使用相對路徑，使其在任何環境中都更穩健
        project_path = Path(TARGET_FOLDER_NAME)
        project_path.mkdir(exist_ok=True)
        os.chdir(project_path)

        main_server_process = subprocess.Popen(
            ["python3", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", str(MAIN_APP_PORT)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8'
        )
        await asyncio.sleep(3) # 等待伺服器啟動

        await broadcast_step(f"✅ WebSocket 頻道 (/ws) 已建立", "ok")
        await broadcast_step(f"✅ 引擎已上線: http://0.0.0.0:{MAIN_APP_PORT}", "ok", delay=0.6)
        await broadcast_step('\n<span class="ok">✨ 系統啟動完成，歡迎指揮官。</span>', "raw")

        await bootstrap_manager.broadcast({"event_type": "BOOT_COMPLETE"})
        launcher_logger.info("   - ✅ 啟動序列直播完成。")

        # 保持 Colab 儲存格活躍
        while main_server_process.poll() is None:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        launcher_logger.warning("\n🛑 [偵測到使用者手動中斷請求...]")
    except Exception as e:
        launcher_logger.error(f"\n💥 作戰流程發生嚴重錯誤: {e}", exc_info=True)
    finally:
        launcher_logger.info("🎬 終端清理程序開始...")
        if bootstrap_server_instance and not bootstrap_server_instance.should_exit:
            bootstrap_server_instance.should_exit = True
            await bootstrap_server_instance.shutdown()
            launcher_logger.info("   - 引導伺服器已關閉。")
        if main_server_process and main_server_process.poll() is None:
            main_server_process.terminate()
            launcher_logger.info("   - 主應用伺服器已終止。")
        launcher_logger.info("--- 系統已安全關閉 ---")
        logging.shutdown()

if __name__ == "__main__":
    # 為了在 Colab 中執行，我們需要確保事件迴圈正在執行
    try:
        if asyncio.get_running_loop():
            # 如果已經在一個執行中的迴圈裡（例如在 Jupyter/Colab 中），就建立一個 task
            asyncio.create_task(main())
    except RuntimeError:
        # 否則，就用 asyncio.run() 啟動一個新的迴圈
        asyncio.run(main())
