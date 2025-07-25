from typing import List
from fastapi import WebSocket

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
