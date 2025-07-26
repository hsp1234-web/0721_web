# ╔══════════════════════════════════════════════════════════════════╗
# ║                  🐍 server_main.py 變更摘要 v2.1 🐍                  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                  ║
# ║  【關鍵修正】                                                    ║
# ║  1. 停用 Uvicorn 預設日誌：在檔案最末端的 `uvicorn.run` 指令中， ║
# ║     新增了 `log_config=None` 參數。                              ║
# ║                                                                  ║
# ║  【修正目的】                                                    ║
# ║     此變更是為了防止 Uvicorn 伺服器自行產生並輸出日誌，確保所有  ║
# ║     的日誌訊息都統一由我們在 `lifespan` 中設定的日誌系統處理。   ║
# ║     這樣一來，前端 `colab_run.py` 的日誌面板才能完全接管螢幕輸出，║
# ║     實現我們設計的「精準指示器」效果。                           ║
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

# --- 核心修正：使用 Lifespan 管理器 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    FastAPI 的生命週期管理器。
    在 yield 之前的程式碼會在應用程式啟動時執行一次。
    在 yield 之後的程式碼會在應用程式關閉時執行一次。
    """
    # --- 日誌設定 (只會執行一次) ---
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / f"日誌-{time.strftime('%Y-%m-%d')}.txt"

    # 簡化且統一的日誌格式
    log_format = '%(asctime)s [%(levelname)s] - %(message)s'
    
    # 移除任何已經存在的 root logger handlers，避免重複添加
    # 這是確保日誌純淨的關鍵步驟
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)

    # 設定日誌系統
    logging.basicConfig(
        level=logging.INFO,
        format=log_format,
        handlers=[
            logging.FileHandler(log_file_path, encoding='utf-8'),
            logging.StreamHandler(sys.stdout) # 輸出到標準輸出，由 colab_run.py 監聽
        ],
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    logging.info("日誌系統初始化完成，日誌將記錄於: %s", log_file_path)

    # --- 環境設定 ---
    base_dir = Path(os.getenv('PHOENIX_HEART_ROOT', '.'))
    logging.info("伺服器基準目錄 (BASE_DIR) 設定為: %s", base_dir.resolve())

    templates_dir = base_dir / "templates"
    logging.info("正在從 %s 載入模板...", templates_dir.resolve())
    
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    # --- Lifespan 的核心 ---
    yield
    # --- 應用程式關閉時執行的程式碼 ---
    logging.info("FastAPI 應用程式正在關閉...")


# --- FastAPI 應用程式實例化 ---
app = FastAPI(lifespan=lifespan)

# --- 路由 (Routes) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    根路由，渲染主儀表板模板。
    """
    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": "鳳凰之心儀表板"})

# --- 主程式進入點 ---
if __name__ == "__main__":
    import uvicorn
    
    print("INFO: 準備在 http://0.0.0.0:8000 上啟動 Uvicorn 伺服器。")
    
    if not os.getenv('PHOENIX_HEART_ROOT'):
        os.environ['PHOENIX_HEART_ROOT'] = os.getcwd()

    # 關鍵修正：新增 log_config=None，將日誌控制權完全交給 FastAPI 的 lifespan
    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
