# ╔══════════════════════════════════════════════════════════════════╗
# ║                🐍 server_main.py 變更摘要 v2.2 🐍                  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                  ║
# ║  【格式變更】                                                    ║
# ║  1. 日誌檔副檔名：將日誌檔的產生格式從 `.txt` 變更為 `.md`。       ║
# ║                                                                  ║
# ║  【變更目的】                                                    ║
# ║     配合您希望歸檔檔案為 Markdown 格式的需求，從源頭統一格式。     ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import os
import sys
import logging
import time
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 的生命週期管理器。
    """
    # --- 路徑設定 ---
    # 取得 main.py 所在的目錄
    base_dir = Path(__file__).parent.resolve()

    # --- 日誌設定 ---
    log_dir = base_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / f"日誌-{time.strftime('%Y-%m-%d')}.md"

    log_format = '%(asctime)s [%(levelname)s] - %(message)s'

    # 清除舊的 handler
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ],
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    logging.info("日誌系統初始化完成，日誌將記錄於: %s", log_file_path)

    # --- 環境與模板設定 ---
    logging.info("伺服器基準目錄 (BASE_DIR) 設定為: %s", base_dir)
    templates_dir = base_dir / "templates"
    logging.info("正在從 %s 載入模板...", templates_dir)
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    yield
    logging.info("FastAPI 應用程式正在關閉...")

app = FastAPI(lifespan=lifespan)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": "鳳凰之心儀表板"})

if __name__ == "__main__":
    import uvicorn
    # 確保工作目錄是 main.py 所在的目錄
    os.chdir(Path(__file__).parent.resolve())
    print("INFO: 準備在 http://0.0.0.0:8000 上啟動 Uvicorn 伺服器。")
    if not os.getenv('PHOENIX_HEART_ROOT'):
        os.environ['PHOENIX_HEART_ROOT'] = os.getcwd()
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
