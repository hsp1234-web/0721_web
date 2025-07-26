# ╔══════════════════════════════════════════════════════════════════╗
# ║             🐍 server_main.py 整合應用程式 v3.0 🐍               ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                  ║
# ║  【架構變更】                                                    ║
# ║  1. **統一日誌**: 從 `core.logging_config` 匯入並使用標準化的日誌設定。║
# ║  2. **整合路由**: 將 `apps` 子應用程式 (`quant`, `transcriber`)   ║
# ║     的路由統一掛載到主應用程式中。                               ║
# ║  3. **簡化設定**: 移除本地日誌設定，使程式碼更清晰。             ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import os
import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

# --- 核心模組匯入 ---
from core.logging_config import setup_logger
from apps.quant.main import router as quant_router
from apps.transcriber.main import router as transcriber_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 的生命週期管理器。
    """
    # --- 日誌設定 ---
    # 使用重構後的標準化日誌設定，並啟用 Markdown 格式
    setup_logger(use_markdown=True)
    logging.info("鳳凰之心伺服器開始啟動...")

    # --- 環境與模板設定 ---
    base_dir = Path(os.getenv('PHOENIX_HEART_ROOT', '.'))
    templates_dir = base_dir / "templates"
    logging.info(f"正在從 {templates_dir.resolve()} 載入模板...")
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    yield

    logging.info("FastAPI 應用程式正在關閉...")

# --- 主應用程式實例 ---
app = FastAPI(
    title="鳳凰之心整合伺服器",
    description="一個整合了量化分析與語音轉錄的 FastAPI 伺服器。",
    version="3.0",
    lifespan=lifespan
)

# --- 掛載子應用程式的路由 ---
app.include_router(quant_router, prefix="/quant", tags=["量化分析"])
app.include_router(transcriber_router, prefix="/transcriber", tags=["語音轉錄"])


# --- 主頁面路由 ---
@app.get("/", response_class=HTMLResponse, tags=["系統"])
async def read_root(request: Request):
    """
    提供一個簡單的 HTML 儀表板頁面。
    """
    templates = request.app.state.templates
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "鳳凰之心儀表板"}
    )

# --- 主程式執行區塊 ---
if __name__ == "__main__":
    import uvicorn
    import argparse

    parser = argparse.ArgumentParser(description="鳳凰之心整合伺服器")
    parser.add_argument("--host", type=str, default="0.0.0.0", help="綁定的主機位址")
    parser.add_argument("--port", type=int, default=8000, help="綁定的埠號")
    parser.add_argument("--no-reload", action="store_true", help="禁用熱重載")
    args = parser.parse_args()

    # 確保在直接執行此檔案時，專案根目錄被正確設定
    if not os.getenv('PHOENIX_HEART_ROOT'):
        os.environ['PHOENIX_HEART_ROOT'] = os.getcwd()

    print(f"INFO: 準備在 http://{args.host}:{args.port} 上啟動 Uvicorn 伺服器。")

    # 使用 uvicorn 啟動應用，並關閉其預設的存取日誌，以避免與我們的設定衝突
    uvicorn.run(
        "server_main:app",
        host=args.host,
        port=args.port,
        log_config=None, # 關鍵：關閉 uvicorn 的預設日誌
        reload=not args.no_reload
    )
