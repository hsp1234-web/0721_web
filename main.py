import asyncio
import json
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from typing import List

from core.config import settings
from core.monitor import PerformanceMonitor
from logger.main import setup_logging, set_websocket_manager

# --- 初始化日誌系統 ---
setup_logging()

# --- 連線管理器 ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # 連線成功後，立即發送當前配置
        await websocket.send_json({
            "event_type": "CONFIG_UPDATE",
            "payload": settings.dict()
        })

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, data: dict):
        for connection in self.active_connections:
            await connection.send_json(data)

manager = ConnectionManager()
monitor = PerformanceMonitor(manager)
set_websocket_manager(manager)

# --- FastAPI 應用程式實例 ---
app = FastAPI(
    title="鳳凰之心-後端引擎 v14.0",
    description="為鳳凰之心前端駕駛艙提供完全參數化服務的後端。",
    version="14.0.0",
)

@app.on_event("startup")
async def startup_event():
    # 在背景啟動性能監控器
    asyncio.create_task(monitor.run())

@app.on_event("shutdown")
def shutdown_event():
    monitor.stop()

# --- WebSocket 端點 ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 這個迴圈是保持連線所必需的
            # 在這個版本中，我們不期望從客戶端收到太多訊息
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("[WebSocket] 一個客戶端已斷開連線。")


# --- 掛載靜態文件服務 ---
app.mount("/", StaticFiles(directory="static", html=True), name="static")
