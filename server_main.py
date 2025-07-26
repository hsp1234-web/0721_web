import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import logging
import time

# 導入我們自己的日誌設定函式
from logger.main import setup_markdown_logger

# 在應用程式啟動前，立刻設定好我們的日誌系統
# 注意：此版本假設日誌路徑等由啟動腳本 (如 Colab) 透過環境變數注入
LOG_DIR = Path(os.environ.get('LOG_ARCHIVE_DIR', './logs')) # 提供一個本地預設值
LOG_FILENAME = os.environ.get('LOG_FILENAME', f"日誌-{time.strftime('%Y-%m-%d')}.md")
setup_markdown_logger(log_dir=LOG_DIR, filename=LOG_FILENAME)

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="鳳凰之心-後端引擎",
    description="提供儀表板介面與核心 API 服務",
    version="2.0.0"
)

logger = logging.getLogger(__name__)

# 路徑解析
BASE_DIR = Path(os.environ.get('PHOENIX_HEART_ROOT', Path.cwd()))
templates_dir = BASE_DIR / "templates"
logger.info(f"伺服器基準目錄 (BASE_DIR) 設定為: {BASE_DIR}")
logger.info(f"正在從 {templates_dir} 載入模板...")

if not templates_dir.is_dir():
    logger.critical(f"致命錯誤：在 {BASE_DIR} 中找不到 'templates' 資料夾！")

templates = Jinja2Templates(directory=str(templates_dir))

@app.on_event("startup")
async def startup_event():
    logger.info("FastAPI 應用程式啟動完成。")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    logger.info(f"接收到來自 {request.client.host} 的儀表板請求。")
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("FASTAPI_PORT", 8000))
    logger.info(f"準備在 http://0.0.0.0:{port} 上啟動 Uvicorn 伺服器。")
    
    # 關鍵修正：移除 reload=True，使用穩定的生產模式啟動
    uvicorn.run("server_main:app", host="0.0.0.0", port=port)
