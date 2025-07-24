# -*- coding: utf-8 -*-
import os
import sys
import importlib
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

# --- 設定日誌 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- App 註冊表 ---
# 用於儲存加載的 App 資訊，以便在前端顯示
APPS_REGISTER = []

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式生命週期管理。
    在啟動時，動態掃描並加載所有 apps。
    """
    logger.info("🚀 伺服器啟動中...")

    # 將專案根目錄加入 sys.path 以便導入 apps
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))

    apps_dir = project_root / "apps"
    if not apps_dir.is_dir():
        logger.warning(f"找不到 'apps' 目錄，將不會加載任何應用。")
        yield
        return

    logger.info(f"掃描 'apps' 目錄: {apps_dir}")
    for app_dir in apps_dir.iterdir():
        if app_dir.is_dir() and (app_dir / "main.py").exists():
            app_name = app_dir.name
            try:
                # 動態導入 app 模組
                module_name = f"apps.{app_name}.main"
                module = importlib.import_module(module_name)

                # 檢查模組中是否有 'router' 和 'app_info'
                if hasattr(module, "router") and hasattr(module, "app_info"):
                    app.include_router(module.router)
                    APPS_REGISTER.append(module.app_info)
                    logger.info(f"✅ 成功加載應用: '{module.app_info.get('name', app_name)}'")
                else:
                    logger.warning(f"🟡 在 '{module_name}' 中找不到 'router' 或 'app_info'，已跳過。")
            except Exception as e:
                logger.error(f"❌ 加載應用 '{app_name}' 失敗: {e}", exc_info=True)

    logger.info("所有應用加載完畢，伺服器準備就緒！")

    # 建立一個測試檔案來驗證 startup 事件
    with open("items.txt", "w") as f:
        f.write("FastAPI startup event test file.")
    logger.info("測試檔案 'items.txt' 已建立。")

    yield
    # --- 關閉時的清理工作 (如果有的話) ---
    logger.info("👋 伺服器正在關閉...")

    # 刪除測試檔案來驗證 shutdown 事件
    if os.path.exists("items.txt"):
        os.remove("items.txt")
        logger.info("測試檔案 'items.txt' 已刪除。")


# --- FastAPI 應用實例 ---
app = FastAPI(
    title="模組化非同步平台",
    description="一個高度模組化、可擴展的平台，支持非同步應用懶加載。",
    version="1.0.0",
    lifespan=lifespan
)

# --- 核心 API 路由 ---
@app.get("/api/apps")
async def get_applications():
    """返回所有已註冊應用的列表。"""
    return APPS_REGISTER

# --- 掛載靜態文件 ---
# 為了提供 index.html 和未來的 CSS/JS 檔案
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """提供平台的主歡迎頁面。"""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        # 提供一個預設的歡迎頁面，以防 index.html 不存在
        return HTMLResponse(content="""
        <!DOCTYPE html>
        <html>
        <head>
            <title>平台正在初始化</title>
        </head>
        <body>
            <h1>歡迎來到模組化平台</h1>
            <p>找不到 'static/index.html'。請確保該檔案存在。</p>
        </body>
        </html>
        """, status_code=200)

    with open(index_path, "r", encoding="utf-8") as f:
        return HTMLResponse(content=f.read(), status_code=200)

if __name__ == "__main__":
    import uvicorn
    # 為了方便直接測試此文件
    logger.info("以直接執行模式啟動 Uvicorn 伺服器...")
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True, # 在開發時啟用重載
        reload_dirs=[str(Path(__file__).parent)]
    )
