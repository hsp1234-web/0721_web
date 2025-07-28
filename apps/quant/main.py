# -*- coding: utf-8 -*-
"""
量化金融 App (Quant) - FastAPI 伺服器入口
"""
import os
import uvicorn
from fastapi import FastAPI
from apps.quant.api.v1 import routes as v1_routes

# --- Lifespan 事件處理 ---
# 使用 FastAPI 推薦的 lifespan 上下文管理器來處理啟動和關閉事件
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在應用程式啟動時執行的程式碼
    print("Quant App 啟動中...")
    yield
    # 在應用程式關閉時執行的程式碼
    print("Quant App 關閉中...")

# --- FastAPI App 實例化 ---
# 建立 FastAPI 應用，並掛載 lifespan 事件處理器
app = FastAPI(
    title="鳳凰之心 - 量化分析服務",
    description="提供量化回測與分析相關的 API",
    version="1.0.0",
    lifespan=lifespan
)

# --- API 路由掛載 ---
# 將 v1 版本的路由掛載到主應用上
app.include_router(v1_routes.router, prefix="/api/v1")

# --- 根路由 ---
@app.get("/", summary="服務健康檢查", tags=["系統"])
async def read_root():
    """
    根路由，用於簡單的服務健康檢查。
    同時回報當前運行的組態參數。
    """
    port = os.environ.get("PORT", "未設定")
    timezone = os.environ.get("TIMEZONE", "未設定")
    return {
        "status": "ok",
        "service": "鳳凰之心 - 量化分析服務",
        "port": port,
        "timezone": timezone,
    }

# --- 主程式入口 ---
if __name__ == "__main__":
    """
    當此腳本被直接執行時，啟動 Uvicorn 伺服器。
    我們從環境變數讀取埠號，以便 launch.py 可以為每個 App 分配不同埠號。
    """
    port = int(os.environ.get("PORT", 8001)) # 預設為 8001
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
