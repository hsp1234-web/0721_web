# 檔案: core/bootstrap_server.py
# 說明: 一個極度輕量化的 FastAPI 伺服器，專用於在主應用依賴安裝期間，
#       即時向前端串流日誌。

import asyncio
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any

# --- 核心邏輯 ---

class BootstrapConnectionManager:
    """
    一個極簡的連線管理器，只處理廣播訊息功能。
    """
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: Dict[str, Any]):
        # 在多個連線上並行發送訊息
        tasks = [connection.send_json(data) for connection in self.active_connections]
        await asyncio.gather(*tasks)

# 建立 FastAPI app 實例和連線管理器
bootstrap_app = FastAPI(
    title="鳳凰之心-引導伺服器",
    description="用於直播重量級依賴安裝過程的輕量級伺服器。",
    version="1.0.0"
)
bootstrap_manager = BootstrapConnectionManager()

@bootstrap_app.websocket("/ws/bootstrap")
async def websocket_endpoint(websocket: WebSocket):
    """
    引導伺服器的唯一 WebSocket 端點。
    """
    await bootstrap_manager.connect(websocket)
    try:
        while True:
            # 保持連線開啟，等待後端廣播日誌
            await websocket.receive_text()
    except WebSocketDisconnect:
        bootstrap_manager.disconnect(websocket)

# --- 啟動函式 ---

async def start_bootstrap_server(port: int, host: str = "0.0.0.0"):
    """
    以程式化的方式啟動 Uvicorn 引導伺服器。
    """
    config = uvicorn.Config(
        bootstrap_app,
        host=host,
        port=port,
        log_level="warning" # 我們不希望引導伺服器本身產生太多日誌
    )
    server = uvicorn.Server(config)

    # 這是關鍵：在背景執行伺服器，這樣主腳本才不會被阻塞
    server_task = asyncio.create_task(server.serve())

    # 給伺服器一點時間啟動
    await asyncio.sleep(1)

    return server, server_task

# --- 直接執行時的測試程式碼 ---
if __name__ == "__main__":
    async def main_test():
        print("正在啟動引導伺服器於 8001 埠...")
        server, _ = await start_bootstrap_server(port=8001)

        print("伺服器已啟動。現在模擬廣播日誌...")
        try:
            count = 0
            while True:
                await asyncio.sleep(2)
                log_data = {
                    "event_type": "INSTALL_LOG",
                    "payload": f"[{count}] 正在安裝套件 'package-{count}'..."
                }
                print(f"廣播: {log_data['payload']}")
                await bootstrap_manager.broadcast(log_data)
                count += 1
        except KeyboardInterrupt:
            print("\n正在關閉伺服器...")
            server.should_exit = True
            await server.shutdown()

    asyncio.run(main_test())
