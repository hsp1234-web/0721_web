import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import os
import logging

# --- 關鍵修改 v2.0 ---
# 導入我們自己的日誌設定函式
from logger.main import setup_markdown_logger

# 從環境變數讀取由指揮中心注入的日誌路徑和檔名
LOG_DIR = Path(os.environ.get('LOG_ARCHIVE_DIR', '/content/作戰日誌歸檔'))
LOG_FILENAME = os.environ.get('LOG_FILENAME', 'fallback-log.md')

# 在應用程式啟動前，立刻設定好我們的日誌系統
setup_markdown_logger(log_dir=LOG_DIR, filename=LOG_FILENAME)

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="鳳凰之心-後端引擎",
    description="提供儀表板介面與核心 API 服務",
    version="2.0.0"
)

# 使用 logging 模組來記錄事件
logger = logging.getLogger(__name__)

# --- 路徑解析 ---
BASE_DIR = Path(os.environ.get('PHOENIX_HEART_ROOT', Path.cwd()))
templates_dir = BASE_DIR / "templates"
logger.info(f"伺服器基準目錄 (BASE_DIR) 設定為: {BASE_DIR}")
logger.info(f"正在從 {templates_dir} 載入模板...")

if not templates_dir.is_dir():
    logger.critical(f"致命錯誤：在 {BASE_DIR} 中找不到 'templates' 資料夾！")

templates = Jinja2Templates(directory=str(templates_dir))

@app.on_event("startup")
async def startup_event():
    """應用程式啟動時執行的事件。"""
    logger.info("FastAPI 應用程式啟動完成。")
    logger.info("儀表板介面已準備就緒。")

@app.on_event("shutdown")
def shutdown_event():
    """應用程式關閉時執行的事件。"""
    logging.info("伺服器正在關閉...日誌歸檔結束。")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    根路徑端點，回傳儀表板 HTML。
    """
    logger.info(f"接收到來自 {request.client.host} 的儀表板請求。")
    return templates.TemplateResponse(
        "dashboard.html", {"request": request}
    )

if __name__ == "__main__":
    port = int(os.environ.get("FASTAPI_PORT", 8000))
    logger.info(f"準備在 http://0.0.0.0:{port} 上啟動 Uvicorn 伺服器。")
    
    # 關鍵修正：移除 reload=True，使用穩定的生產模式啟動
    uvicorn.run("server_main:app", host="0.0.0.0", port=port)
