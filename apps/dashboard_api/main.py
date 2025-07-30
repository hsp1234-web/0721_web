# -*- coding: utf-8 -*-
import asyncio
import json
import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from cachetools import TTLCache, cached
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

# --- 資料庫設定 ---
DB_FILE = Path(os.getenv("DB_FILE", "/tmp/state.db"))

# --- 快取設定 ---
# 為資源使用率設定一個 TTL (Time-To-Live) 快取，快取時間為 1 秒
resource_cache = TTLCache(maxsize=1, ttl=1)

def db_connect():
    """建立資料庫連線"""
    try:
        conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError:
        raise HTTPException(status_code=503, detail="資料庫目前無法訪問，可能正在初始化。")

# --- 資料庫查詢 ---
@cached(resource_cache)
def get_status_from_db():
    """從資料庫獲取狀態，此函數的結果將被快取。"""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM status_table WHERE id = 1")
            status = cursor.fetchone()
            if status:
                return dict(status)
            return None
    except sqlite3.OperationalError:
        return None # 在資料庫鎖定時返回 None

def get_logs_from_db(limit: int = 50, offset: int = 0):
    """從資料庫獲取日誌，支援分頁。"""
    try:
        with db_connect() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM log_table ORDER BY timestamp DESC LIMIT ? OFFSET ?",
                (limit, offset)
            )
            logs = cursor.fetchall()
            return [dict(log) for log in logs]
    except sqlite3.OperationalError:
        return [] # 資料庫鎖定時返回空列表

# --- FastAPI Lifespan ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("API 服務啟動...")
    yield
    print("API 服務關閉...")

# --- FastAPI 應用實例 ---
app = FastAPI(lifespan=lifespan)

# --- API 端點 ---
@app.get("/api/status")
async def get_status():
    """
    獲取系統的完整狀態。
    高頻數據 (CPU/RAM) 會從快取中讀取。
    """
    status_data = get_status_from_db()
    if not status_data:
        return JSONResponse(
            content={"status": "initializing", "message": "系統正在啟動中，請稍候..."},
            status_code=202 # Accepted
        )
    return JSONResponse(content=status_data)

@app.get("/api/logs")
async def get_logs(limit: int = 50, offset: int = 0):
    """
    獲取日誌，支援分頁。
    - `limit`: 回傳的日誌數量上限
    - `offset`: 從第幾筆日誌開始回傳
    """
    logs = get_logs_from_db(limit, offset)
    return JSONResponse(content=logs)

@app.get("/api/health")
async def health_check():
    """提供一個健康檢查端點。"""
    return JSONResponse(content={"status": "ok"})

# --- 主執行區塊 ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8004))
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=port)
