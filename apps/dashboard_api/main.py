# -*- coding: utf-8 -*-
from fastapi import FastAPI
from fastapi.responses import JSONResponse
import uvicorn
import os
import json
from pathlib import Path
import asyncio
from contextlib import asynccontextmanager

# --- 全域狀態 ---
# 使用一個字典來儲存應用的記憶體狀態，這樣更具擴充性
app_state = {"action_url": None, "status": "pending"}
STATE_FILE = Path(os.getenv("STATE_FILE", "/tmp/phoenix_state.json"))

# --- 背景任務 ---
async def monitor_state_file():
    """一個異步的背景任務，定期檢查狀態檔案並更新全域 app_state。"""
    while True:
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    data = json.load(f)
                # 假設狀態檔案的格式為 {"status": "success", "url": "..."}
                if data.get("status") == "success" and data.get("url"):
                    app_state["action_url"] = data["url"]
                    app_state["status"] = "success"
                    # 成功獲取後可以停止輪詢，或者繼續以備未來更新
                    # 這裡我們選擇在成功後停止，以節省資源
                    break
            except (json.JSONDecodeError, IOError):
                # 檔案可能正在被寫入或尚未完整，忽略錯誤並在下次循環重試
                pass
        await asyncio.sleep(1) # 每秒檢查一次

# --- Lifespan 事件處理器 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 應用啟動時
    print("API 服務啟動，開始監控狀態檔案...")
    # 建立並啟動背景任務
    monitor_task = asyncio.create_task(monitor_state_file())
    yield
    # 應用關閉時
    print("API 服務關閉，正在清理...")
    monitor_task.cancel()

# --- FastAPI 應用實例 ---
app = FastAPI(lifespan=lifespan)

# --- API 端點 ---
@app.get("/api/get-action-url")
async def get_action_url():
    """從記憶體中讀取狀態，並立即返回。"""
    if app_state["status"] == "success":
        return JSONResponse(content={"status": "success", "url": app_state["action_url"]})
    else:
        return JSONResponse(content={"status": "pending"}, status_code=404)

@app.get("/api/health")
async def health_check():
    """提供一個健康檢查端點，用於診斷。"""
    return JSONResponse(content={
        "status": "ok",
        "monitoring_file": str(STATE_FILE),
        "file_exists": STATE_FILE.exists(),
        "current_app_state": app_state
    })

# --- 主執行區塊 ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    uvicorn.run(app, host="0.0.0.0", port=port)
