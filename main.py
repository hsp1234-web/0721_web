import asyncio
import json
import logging
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from core.monitor import SYSTEM_EVENTS_QUEUE, PerformanceMonitor
from core.presentation_manager import PresentationManager

# --- App Initialization ---
app = FastAPI(title="鳳凰之心後端指揮中心")
presentation_manager = PresentationManager()
monitor = PerformanceMonitor(refresh_interval=1.0)

# --- Connection Manager ---
class ConnectionManager:
    """管理所有活躍的 WebSocket 連線。"""
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"新連線: {websocket.client}. 目前連線數: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logging.info(f"斷開連線: {websocket.client}. 目前連線數: {len(self.active_connections)}")

    async def broadcast_json(self, payload: dict):
        """將 JSON 負載廣播給所有連線中的客戶端。"""
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logging.warning(f"廣播失敗: {e} for client {connection.client}")

manager = ConnectionManager()

# --- Background Task: Event Broadcaster ---
async def event_broadcaster():
    """
    這是一個背景執行的長時任務。
    它會不斷地從中央事件佇列中讀取事件，
    並將其廣播給所有已連接的 WebSocket 客戶端。
    """
    logging.info("事件廣播器已啟動...")
    while True:
        try:
            event = await SYSTEM_EVENTS_QUEUE.get()

            # 這裡可以根據事件類型進行不同的處理
            # 目前，我們將所有事件都傳遞給 PresentationManager
            # 未來可以擴展，例如，某些事件只記錄，不更新 UI

            if event["type"] == "PERFORMANCE_UPDATE":
                # 對於性能更新，我們可能需要合併一些數據
                # 但目前架構是 PresentationManager 處理所有事
                pass

            # 這是一個簡化範例，我們假設所有事件都觸發儀表板更新
            # 在一個更複雜的應用中，你可能只想在有日誌時更新日誌部分
            # 但為了儀表板的即時性，每次更新所有內容是最簡單的做法

            # 從事件中提取數據
            stats_data = {
                "cpu": event.get("data", {}).get("cpu", 0),
                "ram": event.get("data", {}).get("ram", 0),
                "log": event.get("data") if event.get("type") == "LOG_MESSAGE" else None,
                "time": event.get("timestamp"),
                 # 模擬服務狀態
                "services": [
                    {"name": "後端 FastAPI 引擎", "status": "ok"},
                    {"name": "WebSocket 通訊頻道", "status": "ok"},
                ]
            }

            js_command = presentation_manager.get_dashboard_update_js(stats_data)

            payload = {"action": "execute_js", "js_code": js_command}
            await manager.broadcast_json(payload)

            SYSTEM_EVENTS_QUEUE.task_done()

        except Exception as e:
            logging.error(f"事件廣播器發生錯誤: {e}", exc_info=True)
            # 防止因單次錯誤而導致整個廣播迴圈崩潰
            await asyncio.sleep(1)


# --- FastAPI App Events ---
@app.on_event("startup")
async def startup_event():
    """在應用啟動時執行的動作。"""
    logging.info("後端應用程式啟動...")
    # 啟動背景性能監控
    monitor.start()
    # 啟動背景事件廣播器
    asyncio.create_task(event_broadcaster())

@app.on_event("shutdown")
async def shutdown_event():
    """在應用關閉時執行的動作。"""
    logging.info("後端應用程式關閉...")
    await monitor.stop()


# --- HTTP Routes ---
@app.get("/", response_class=HTMLResponse)
async def get_dashboard():
    """提供儀表板的 HTML 頁面。"""
    # 從 PresentationManager 獲取 HTML 內容
    html_content = presentation_manager.get_initial_html_structure()
    return HTMLResponse(content=html_content)


# --- WebSocket Endpoint ---
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # 等待來自客戶端的訊息
            data = await websocket.receive_text()
            message = json.loads(data)

            if message.get("type") == "FRONTEND_READY":
                logging.info("前端已就緒，正在傳送啟動序列...")
                # 當前端準備好時，發送啟動動畫的 JS 指令
                boot_sequence_js_list = presentation_manager.get_boot_sequence_js()
                for js_command in boot_sequence_js_list:
                    payload = {"action": "execute_js", "js_code": js_command}
                    await websocket.send_json(payload)
                    # 在指令之間短暫暫停，以模擬真實的啟動延遲
                    await asyncio.sleep(0.1)
                logging.info("啟動序列傳送完畢。")

    except WebSocketDisconnect:
        logging.warning("客戶端斷開連線 (WebSocketDisconnect)")
    except Exception as e:
        logging.error(f"WebSocket 發生未知錯誤: {e}", exc_info=True)
    finally:
        manager.disconnect(websocket)
