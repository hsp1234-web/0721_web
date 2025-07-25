import importlib
import os
import sys
from typing import Dict

from typing import List

from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect
from fastapi.routing import APIRoute
from fastapi.staticfiles import StaticFiles

# 將專案根目錄加入 sys.path，確保無論從哪裡啟動都能正確找到模組
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from logger.main import setup_logging


# --- 初始化日誌系統 ---
# 這必須在應用程式實例化之前完成，以捕獲啟動日誌
setup_logging()


# --- 應用程式實例 ---
app = FastAPI(
    title="鳳凰之心-後端引擎",
    description="一個現代化、可維護的後端架構，為鳳凰之心前端駕駛艙提供服務。",
    version="2.0.0",
)


# --- WebSocket 連線管理器 ---
class ConnectionManager:
    """管理所有 WebSocket 連線，並提供廣播功能。"""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """接受一個新的 WebSocket 連線。"""
        await websocket.accept()
        self.active_connections.append(websocket)
        print(f"[WebSocket 管理器] 新增連線。目前連線數: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """斷開一個 WebSocket 連線。"""
        self.active_connections.remove(websocket)
        print(f"[WebSocket 管理器] 移除連線。目前連線數: {len(self.active_connections)}")

    async def broadcast(self, message: str) -> None:
        """將訊息廣播給所有已連線的客戶端。"""
        for connection in self.active_connections:
            await connection.send_text(message)


manager = ConnectionManager()


# --- WebSocket 端點 ---
@app.websocket("/ws/logs")
async def websocket_endpoint(websocket: WebSocket):
    """處理日誌的 WebSocket 端點。"""
    await manager.connect(websocket)
    try:
        while True:
            # 我們在這裡不接收任何訊息，只做單向廣播
            # 但這個迴圈是保持連線所必需的
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("[WebSocket 端點] 一個客戶端已斷開連線。")


# --- 動態路由掃描與聚合 ---
APPS_DIR = "apps"

print("[應用主入口] 開始掃描業務邏輯單元 (apps)...")

for app_name in os.listdir(APPS_DIR):
    app_path = os.path.join(APPS_DIR, app_name)

    if os.path.isdir(app_path) and not app_name.startswith("__"):
        router_module_path = f"{APPS_DIR}.{app_name}.main"

        try:
            router_module = importlib.import_module(router_module_path)

            if hasattr(router_module, "router"):
                print(f"  -> 發現並註冊路由: {app_name}")
                router_instance = getattr(router_module, "router")
                if isinstance(router_instance, APIRouter):
                    app.include_router(
                        router_instance,
                        prefix=f"/{app_name}",
                        tags=[app_name.capitalize()],
                    )
            else:
                print(f"  -! 在 {router_module_path} 中找不到 'router' 物件。")

        except ImportError as e:
            print(f"  -! 無法從 {app_name} 匯入路由: {e}")
        except Exception as e:
            print(f"  -! 處理 {app_name} 時發生未知錯誤: {e}")

print("[應用主入口] 所有路由掃描完畢。")

# --- 診斷資訊：打印所有已註冊的路由 ---
print("[應用主入口] --- 已註冊的 API 路由 ---")
for route in app.routes:
    if isinstance(route, APIRoute):
        methods = ", ".join(route.methods)
        print(f"  - 路徑: {route.path}, 方法: {{{methods}}}, 名稱: {route.name}")
    else:
        # For mounted sub-applications, etc.
        print(f"  - 掛載點/路由: {route}")
print("[應用主入口] --- 路由列表結束 ---")


# --- 掛載靜態文件服務 ---
# 這是最後一步，確保它不會覆蓋任何已定義的 API 路由
app.mount("/", StaticFiles(directory="static", html=True), name="static")
