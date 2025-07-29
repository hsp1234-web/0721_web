# -*- coding: utf-8 -*-
"""
量化金融 App (Quant) - FastAPI 伺服器入口
"""
import os
import sys
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI

# --- 設置導入路徑 ---
# 將 'apps' 目錄添加到 sys.path
# 這樣 `from quant.api.v1 import routes as v1_routes` 才能正確工作
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from quant.api.v1 import routes as v1_routes
from quant.logic import database

# 建立 FastAPI 應用實例
app = FastAPI(
    title="鳳凰之心 - 量化金融服務 (Quant App)",
    description="一個獨立的微服務，負責執行金融數據分析、回測與策略計算。",
    version="1.0.0",
)


# --- Lifespan 事件處理 ---
# 使用 FastAPI 推薦的 lifespan 上下文管理器來處理啟動和關閉事件
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 在應用程式啟動時執行的程式碼
    print("量化服務啟動...")
    yield
    # 在應用程式關閉時執行的程式碼
    print("量化服務正在關閉，關閉資料庫連接...")
    database.db_manager.close()

# 建立 FastAPI 應用實例，並傳入 lifespan 管理器
app = FastAPI(
    title="鳳凰之心 - 量化金融服務 (Quant App)",
    description="一個獨立的微服務，負責執行金融數據分析、回測與策略計算。",
    version="1.0.0",
    lifespan=lifespan
)

# --- 包含 API 路由 ---
# 將 v1 版本的路由包含到主應用中
app.include_router(v1_routes.router)

# --- 根路由與健康檢查 ---
@app.get("/", summary="根目錄")
def read_root():
    return {"message": "歡迎來到量化金融服務 API"}

@app.get("/health", summary="服務健康檢查")
def health_check():
    """
    一個簡單的健康檢查端點，用於確認服務是否正在運行。
    """
    return {"status": "ok", "message": "量化金融服務運行中"}

# --- 伺服器啟動函式 ---
def start():
    """
    使用 uvicorn 啟動伺服器。
    這個函式將被 launch.py 呼叫。
    我們從環境變數讀取埠號，以便 launch.py 可以為每個 App 分配不同埠號。
    """
    port = int(os.environ.get("PORT", 8001)) # 預設為 8001
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    # 這使得我們可以獨立運行這個 App 進行測試
    # 在終端機中執行 `python apps/quant/main.py`
    print("正在以獨立模式啟動量化金融伺服器...")
    start()
