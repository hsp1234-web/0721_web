# -*- coding: utf-8 -*-
import asyncio
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

import aiofiles
import aiosqlite
import psutil
from fastapi import FastAPI, File, HTTPException, UploadFile

# --- 全域設定與常數 ---
DATABASE_FILE = Path("app_data.db")
UPLOAD_DIR = Path("uploads")
PROMETHEUS_RUN_SCRIPT = "ALL_DATE/0709_wolf_88/run.py"
PROMETHEUS_PROJECT_DIR = "ALL_DATE/0709_wolf_88"

# 最小所需磁碟空間 (MB)
MIN_DISK_SPACE_MB = 100
# 最大可接受記憶體使用率 (%)
MAX_MEMORY_USAGE_PERCENT = 95


# --- 環境檢查模組 ---
class EnvironmentError(Exception):
    """自訂環境錯誤異常"""
    pass

def check_disk_space():
    """檢查剩餘磁碟空間是否充足。"""
    free_space_mb = psutil.disk_usage('/').free / (1024 * 1024)
    if free_space_mb < MIN_DISK_SPACE_MB:
        raise EnvironmentError(f"磁碟空間不足！剩餘 {free_space_mb:.2f} MB。")
    print(f"磁碟空間檢查通過。剩餘 {free_space_mb:.2f} MB。")

def check_memory():
    """檢查記憶體使用率是否在可接受範圍內。"""
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > MAX_MEMORY_USAGE_PERCENT:
        raise EnvironmentError(f"記憶體使用率過高！目前為 {memory_percent}%。")
    print(f"記憶體檢查通過。目前使用率 {memory_percent}%。")


# --- 資料庫模組 ---
async def initialize_database():
    """建立資料庫和所需的資料表。"""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transcription_tasks (
                id TEXT PRIMARY KEY,
                original_filepath TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                log_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print(f"資料庫 '{DATABASE_FILE}' 已成功初始化。")

# --- 動態插件載入 ---
def load_plugins(app: FastAPI):
    """動態掃描 'apps' 目錄並載入所有插件的路由器。"""
    apps_dir = Path("apps")
    if not apps_dir.is_dir():
        print("⚠️ 'apps' 目錄不存在，跳過插件載入。")
        return

    # 從環境變數讀取要載入的特定插件
    apps_to_load_str = os.getenv("APPS_TO_LOAD")
    apps_to_load = apps_to_load_str.split(',') if apps_to_load_str else None

    if apps_to_load:
        print(f"ℹ️ 指定載入插件: {apps_to_load}")
    else:
        print("ℹ️ 未指定特定插件，將嘗試載入所有插件。")

    for plugin_dir in apps_dir.iterdir():
        if plugin_dir.is_dir() and not plugin_dir.name.startswith('_'):
            # 如果指定了要載入的插件，則只載入列表中的插件
            if apps_to_load and plugin_dir.name not in apps_to_load:
                continue

            try:
                # 動態導入插件的 main 模組
                module_name = f"apps.{plugin_dir.name}.main"
                plugin_module = __import__(module_name, fromlist=["router"])

                # 假設每個插件都有一個名為 'router' 的 APIRouter
                if hasattr(plugin_module, "router"):
                    app.include_router(plugin_module.router, prefix=f"/{plugin_dir.name}", tags=[plugin_dir.name])
                    print(f"✅ 成功載入插件: {plugin_dir.name}")
                else:
                    print(f"⚠️ 在插件 {plugin_dir.name} 中找不到 'router'。")
            except ImportError as e:
                print(f"❌ 載入插件 {plugin_dir.name} 失敗: {e}")


# --- FastAPI 生命週期事件 ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """處理應用程式啟動與關閉事件。"""
    print("--- 應用程式啟動流程開始 ---")
    # 1. 建立所需目錄
    UPLOAD_DIR.mkdir(exist_ok=True)

    # 2. 執行環境檢查
    try:
        print("步驟 1/3: 執行環境檢查...")
        check_disk_space()
        check_memory()
        print("環境檢查通過。")
    except EnvironmentError as e:
        print(f"致命錯誤：環境檢查失敗，無法啟動應用程式。原因：{e}")
        raise RuntimeError(f"環境檢查失敗: {e}") from e

    # 3. 初始化資料庫
    try:
        print("步驟 2/3: 初始化資料庫...")
        await initialize_database()
        print("資料庫初始化完成。")
    except Exception as e:
        print(f"致命錯誤：資料庫初始化失敗。原因：{e}")
        raise RuntimeError(f"資料庫初始化失敗: {e}") from e

    # 4. 載入插件
    print("步驟 3/3: 載入應用插件...")
    load_plugins(app)

    print("--- 應用程式已成功啟動 ---")
    yield
    print("--- 應用程式正在關閉 ---")


# --- FastAPI 應用程式實例 ---
app = FastAPI(lifespan=lifespan)


# --- API 端點 ---

# 核心端點
@app.get("/health", status_code=200, tags=["Core"])
async def health_check() -> dict[str, str]:
    """健康檢查端點。"""
    return {"status": "ok", "message": "服務運行中"}


# --- Uvicorn 啟動 (如果直接執行此檔案) ---
if __name__ == "__main__":
    import uvicorn
    # 為了方便本地測試，我們手動設定環境變數
    # os.environ["APPS_TO_LOAD"] = "transcriber,quant"
    uvicorn.run(app, host="0.0.0.0", port=8000)
