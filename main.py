import asyncio
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

# --- Connection Managers ---
class ConnectionManager:
    """管理一組活躍的 WebSocket 連線。"""
    def __init__(self, name: str):
        self.active_connections: List[WebSocket] = []
        self.name = name
        logging.info(f"'{self.name}' 連線管理器已初始化。")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logging.info(f"[{self.name}] 新連線: {websocket.client}. 目前連線數: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logging.info(f"[{self.name}] 斷開連線: {websocket.client}. 目前連線數: {len(self.active_connections)}")

    async def broadcast_json(self, payload: dict):
        """將 JSON 負載廣播給所有連線中的客戶端。"""
        if not self.active_connections:
            return
        for connection in self.active_connections:
            try:
                await connection.send_json(payload)
            except Exception as e:
                logging.warning(f"[{self.name}] 廣播失敗: {e} for client {connection.client}")

# 為不同的端點建立不同的管理器實例
boot_manager = ConnectionManager("BootServer")
dashboard_manager = ConnectionManager("Dashboard")

# --- Background Task: Dashboard Event Broadcaster ---
async def dashboard_event_broadcaster():
    """
    這個背景任務負責處理儀表板的即時數據更新。
    它從事件佇列中讀取事件，並將其廣播給所有連接到儀表板的客戶端。
    """
    logging.info("儀表板事件廣播器已啟動...")
    while True:
        try:
            event = await SYSTEM_EVENTS_QUEUE.get()

            if event["type"] == "PERFORMANCE_UPDATE":
                stats_data = {
                    "cpu": event.get("data", {}).get("cpu", 0),
                    "ram": event.get("data", {}).get("ram", 0),
                    "log": None,
                    "time": event.get("timestamp"),
                    "services": [
                        {"name": "後端 FastAPI 引擎", "status": "ok"},
                        {"name": "WebSocket 通訊頻道", "status": "ok"},
                    ]
                }
                js_command = presentation_manager.get_dashboard_update_js(stats_data)
                payload = {"action": "execute_js", "js_code": js_command}
                await dashboard_manager.broadcast_json(payload)

            elif event["type"] == "LOG_MESSAGE":
                 stats_data = {
                    "log": event.get("data"),
                    "time": event.get("timestamp"),
                }
                 js_command = presentation_manager.get_dashboard_update_js(stats_data)
                 payload = {"action": "execute_js", "js_code": js_command}
                 await dashboard_manager.broadcast_json(payload)


            SYSTEM_EVENTS_QUEUE.task_done()
        except Exception as e:
            logging.error(f"儀表板廣播器發生錯誤: {e}", exc_info=True)
            await asyncio.sleep(1)


# --- FastAPI App Events ---
@app.on_event("startup")
async def startup_event():
    """在應用啟動時執行的動作。"""
    logging.info("主應用程式啟動...")
    # 啟動背景性能監控
    monitor.start()
    # 啟動背景事件廣播器
    asyncio.create_task(dashboard_event_broadcaster())

@app.on_event("shutdown")
async def shutdown_event():
    """在應用關閉時執行的動作。"""
    logging.info("後端應用程式關閉...")
    await monitor.stop()


# --- HTTP Routes ---
@app.get("/", response_class=HTMLResponse)
async def get_root():
    """
    提供主 HTML 頁面。
    這個頁面包含了連接到引導伺服器的邏輯。
    """
    # 注意：我們不再從 PresentationManager 生成 HTML。
    # HTML 現在是位於 templates/ 檔案夾中的一個靜態檔案。
    # FastAPI 會自動尋找並提供這個檔案。
    # 為了讓它運作，我們需要設定靜態檔案目錄。
    try:
        with open("templates/dashboard.html", "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="<h1>錯誤：找不到 templates/dashboard.html</h1>", status_code=500)


# --- WebSocket Endpoints ---

@app.websocket("/ws/boot")
async def websocket_boot_endpoint(websocket: WebSocket):
    """
    此端點用於處理「啟動序列」的事件廣播。
    它只接受連線，然後由後端（例如 run.py）單向廣播事件。
    """
    await boot_manager.connect(websocket)
    try:
        # 這個端點主要是被動的，等待後端廣播。
        # 我們可以保持連線開放以接收廣播。
        while True:
            # 我們不需要從客戶端接收任何訊息，所以我們可以只是等待。
            # receive_text() 會保持連線開放，直到客戶端斷開。
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.warning(f"[BootServer] 客戶端斷開連線: {websocket.client}")
    except Exception as e:
        logging.error(f"[BootServer] WebSocket 發生錯誤: {e}", exc_info=True)
    finally:
        boot_manager.disconnect(websocket)


@app.websocket("/ws/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    此端點用於處理啟動完成後的「儀表板」即時數據。
    """
    await dashboard_manager.connect(websocket)
    try:
        while True:
            # 等待來自客戶端的訊息 (雖然目前我們不處理任何訊息)
            await websocket.receive_text()
    except WebSocketDisconnect:
        logging.warning(f"[Dashboard] 客戶端斷開連線: {websocket.client}")
    except Exception as e:
        logging.error(f"[Dashboard] WebSocket 發生錯誤: {e}", exc_info=True)
    finally:
        dashboard_manager.disconnect(websocket)
