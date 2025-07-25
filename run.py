import asyncio
import json
import subprocess
import sys
import time
import webbrowser
from threading import Thread
import websockets

# --- 組態設定 ---
HOST = "127.0.0.1"
BOOT_PORT = 8001
APP_PORT = 8000
BOOT_WEBSOCKET_URL = f"ws://{HOST}:{BOOT_PORT}/ws/boot"
APP_URL = f"http://{HOST}:{APP_PORT}"

# --- 輔助函式 ---
def print_header(title):
    print("\n" + "="*60)
    print(f"🎬 {title}")
    print("="*60)

def print_success(message):
    print(f"✅ {message}")

def print_info(message):
    print(f"ℹ️  {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

class BootstrapBroadcaster:
    """一個簡單的 WebSocket 客戶端，用於向引導伺服器廣播事件。"""
    def __init__(self, uri):
        self.uri = uri
        self.websocket = None

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.uri)
            print_success(f"成功連接到引導伺服器: {self.uri}")
        except Exception as e:
            print_error(f"無法連接到引導伺服器: {e}")
            raise

    async def broadcast(self, event: dict):
        if not self.websocket:
            print_error("廣播失敗：WebSocket 未連接。")
            return
        try:
            await self.websocket.send(json.dumps(event))
        except Exception as e:
            print_error(f"廣播事件失敗: {e}")

    async def close(self):
        if self.websocket:
            await self.websocket.close()
            print_info("與引導伺服器的連線已關閉。")


async def run_boot_sequence(broadcaster: BootstrapBroadcaster):
    # ... [啟動序列內容不變] ...
    print_header("開始直播啟動序列")
    await asyncio.sleep(1) # 等待前端連線
    steps = [
        {'event_type': 'BOOT_STEP', 'payload': {'text': '>>> 鳳凰之心 v14.0 最終定稿 啟動序列 <<<', 'type': 'header'}},
        {'event_type': 'BOOT_STEP', 'payload': {'text': '===================================================', 'type': 'dim'}},
        {'event_type': 'BOOT_STEP', 'payload': {'text': '✅ 核心初始化完成', 'type': 'ok'}},
        {'event_type': 'BOOT_STEP', 'payload': {'text': '⏳ 正在掃描硬體介面...', 'type': 'battle'}},
        {'event_type': 'BOOT_STEP', 'payload': {'text': '✅ 硬體掃描完成', 'type': 'ok'}},
    ]
    for step in steps:
        await broadcaster.broadcast(step)
        await asyncio.sleep(0.2)
    await broadcaster.broadcast({'event_type': 'BOOT_STEP', 'payload': {'text': '--- 正在安裝核心依賴 ---', 'type': 'header'}})
    await asyncio.sleep(0.5)
    deps = [
        {'name': 'fastapi', 'size': '1.2MB'},
        {'name': 'uvicorn', 'size': '0.8MB'},
        {'name': 'websockets', 'size': '0.5MB'},
        {'name': 'psutil', 'size': '0.3MB'}
    ]
    for dep in deps:
        await broadcaster.broadcast({'event_type': 'BOOT_PROGRESS_START', 'payload': {'name': dep['name'], 'size': dep['size']}})
        for progress in range(0, 101, 10):
            await broadcaster.broadcast({'event_type': 'BOOT_PROGRESS_UPDATE', 'payload': {'name': dep['name'], 'progress': progress}})
            await asyncio.sleep(0.05)
    print_info("依賴安裝直播完成。")
    await broadcaster.broadcast({'event_type': 'BOOT_STEP', 'payload': {'text': '--- 正在執行系統預檢 ---', 'type': 'header'}})
    await asyncio.sleep(0.5)
    disk_check_rows = [
        ['總空間', ':', '10.0 GB'],
        ['已使用', ':', '6.0 GB'],
        ['剩餘空間', ':', '<span class="highlight">4.0 GB</span>'],
        ['套件需求', ':', '5.0 GB (大型語言模型 v2)'],
        ['狀態', ':', '<span class="error">❌ 空間不足</span>']
    ]
    await broadcaster.broadcast({
        'event_type': 'BOOT_TABLE',
        'payload': {
            'title': '🛡️ 大型套件磁碟空間預檢報告',
            'rows': disk_check_rows
        }
    })
    print_info("系統預檢直播完成。")
    await asyncio.sleep(1)
    final_steps = [
        {'event_type': 'BOOT_STEP', 'payload': {'text': '⏳ 啟動 FastAPI 引擎...', 'type': 'battle'}},
        {'event_type': 'BOOT_STEP', 'payload': {'text': '✅ WebSocket 頻道 (/ws/dashboard) 已規劃', 'type': 'ok'}},
        {'event_type': 'BOOT_STEP', 'payload': {'text': f'✅ 主引擎將於 http://{HOST}:{APP_PORT} 上線', 'type': 'ok'}},
        {'event_type': 'BOOT_STEP', 'payload': {'text': '\n<span class="ok">✨ 系統啟動完成，歡迎指揮官。</span>', 'type': 'raw'}},
    ]
    for step in final_steps:
        await broadcaster.broadcast(step)
        await asyncio.sleep(0.3)
    await broadcaster.broadcast({'event_type': 'BOOT_COMPLETE'})
    print_success("啟動序列直播完成！")

def get_python_executable() -> str:
    """獲取當前正在運行的 Python 解釋器路徑。"""
    return sys.executable

def stream_reader(stream, prefix):
    """讀取並印出流的內容。"""
    for line in iter(stream.readline, b''):
        print(f"[{prefix}] {line.decode().strip()}")
    stream.close()

def launch_bootstrap_server():
    """在背景啟動引導伺服器，並確保它使用正確的 Python 環境。"""
    print_header("啟動引導伺服器")
    try:
        python_executable = get_python_executable()
        print_info(f"使用 Python 解釋器: {python_executable}")

        cmd = [
            python_executable,
            "-m", "uvicorn",
            "main:app",
            "--host", HOST,
            "--port", str(BOOT_PORT),
        ]
        print_info(f"正在執行命令: {' '.join(cmd)}")
        server_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        print_success(f"引導伺服器已在背景啟動 (PID: {server_process.pid})。")

        # 啟動線程來讀取輸出
        Thread(target=stream_reader, args=(server_process.stdout, "UVICORN_OUT"), daemon=True).start()
        Thread(target=stream_reader, args=(server_process.stderr, "UVICORN_ERR"), daemon=True).start()

        return server_process
    except Exception as e:
        print_error(f"啟動引導伺服器失敗: {e}")
        return None

def open_browser():
    """打開瀏覽器以查看啟動畫面。"""
    url = f"http://{HOST}:{BOOT_PORT}"
    print_info(f"在瀏覽器中打開 {url} 以觀看啟動直播...")
    try:
        webbrowser.open(url)
    except Exception:
        print_warning("無法自動打開瀏覽器。請手動訪問以上網址。")


def main():
    """主執行函式。"""
    server_process = launch_bootstrap_server()
    if not server_process:
        sys.exit(1)

    # 等待伺服器完全啟動
    time.sleep(4)
    # 在背景線程中打開瀏覽器，避免阻塞主流程
    Thread(target=open_browser, daemon=True).start()

    broadcaster = BootstrapBroadcaster(BOOT_WEBSOCKET_URL)

    async def main_async():
        """將所有異步操作包裹在同一個事件循環中管理。"""
        try:
            await broadcaster.connect()
            await run_boot_sequence(broadcaster)
        except Exception as e:
            print_error(f"執行異步任務時發生錯誤: {e}")
        finally:
            # 確保 close 操作在同一個事件循環中執行
            await broadcaster.close()

    try:
        # 執行主要的異步邏輯
        asyncio.run(main_async())

        print_header("操作完成")
        print_success("真實啟動序列已成功直播。")
        print_info("引導伺服器將在 5 秒後自動關閉。")
        time.sleep(5)

    except KeyboardInterrupt:
        print_warning("\n偵測到手動中斷，正在清理資源...")
    except Exception as e:
        print_error(f"執行主函式時發生未知錯誤: {e}")
    finally:
        # 在所有操作完成後，終止背景伺服器進程
        if server_process.poll() is None: # 檢查進程是否仍在執行
            server_process.terminate()
            server_process.wait()
            print_success("引導伺服器已關閉。")


if __name__ == "__main__":
    main()
