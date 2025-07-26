# ╔══════════════════════════════════════════════════════════════════╗
# ║                    🐍 server_main.py 變更摘要 🐍                   ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                  ║
# ║  1. 導入 Lifespan 管理器：從 FastAPI 導入 `asynccontextmanager`   ║
# ║     並定義了一個名為 `lifespan` 的非同步函式。                   ║
# ║                                                                  ║
# ║  2. 修正重複初始化問題：                                         ║
# ║     - 將所有日誌設定的相關程式碼，從全域範圍移動到 `lifespan`     ║
# ║       函式內部。                                                 ║
# ║     - 這確保了日誌系統只會在 FastAPI 應用程式啟動時「執行一次」，║
# ║       徹底解決了日誌重複輸出的根源問題。                         ║
# ║                                                                  ║
# ║  3. 解決 DeprecationWarning：                                    ║
# ║     - 移除了舊的 `@app.on_event("startup")` 裝飾器。             ║
# ║     - 在建立 FastAPI 實例時，透過 `app = FastAPI(lifespan=lifespan)`║
# ║       註冊了新的生命週期管理器，這是目前官方推薦的最佳實踐。     ║
# ║                                                                  ║
# ║  4. 統一且簡化的日誌格式：                                       ║
# ║     - 重新設定了日誌的輸出格式為 `[時間] [等級] - 訊息`，使其     ║
# ║       在前端的日誌面板中更加清晰易讀。                           ║
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
    # 從環境變數讀取根目錄，如果沒有則使用當前工作目錄
    # 這使得伺服器更加獨立，不依賴於啟動它的腳本
    base_dir = Path(os.getenv('PHOENIX_HEART_ROOT', '.'))
    logging.info("伺服器基準目錄 (BASE_DIR) 設定為: %s", base_dir.resolve())

    templates_dir = base_dir / "templates"
    logging.info("正在從 %s 載入模板...", templates_dir.resolve())
    
    # 將模板引擎的設定也放在 lifespan 中，確保所有啟動相關的設定都在一起
    # 並將其附加到 app.state，以便在整個應用程式中訪問
    app.state.templates = Jinja2Templates(directory=str(templates_dir))

    # --- Lifespan 的核心 ---
    # 在 yield 之前的程式碼，會在應用程式啟動時執行
    yield
    # 在 yield 之後的程式碼，會在應用程式關閉時執行
    logging.info("FastAPI 應用程式正在關閉...")


# --- FastAPI 應用程式實例化 ---
# 核心修正：將 lifespan 函式傳遞給 FastAPI 的構造函數
app = FastAPI(lifespan=lifespan)

# --- 路由 (Routes) ---
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    根路由，渲染主頁模板。
    """
    # 從 app.state 獲取模板引擎實例，這是透過 lifespan 設定的
    templates = request.app.state.templates
    return templates.TemplateResponse("dashboard.html", {"request": request, "title": "鳳凰之心儀表板"})

# --- 主程式進入點 ---
if __name__ == "__main__":
    import uvicorn
    
    # 這段程式碼主要用於在本機直接執行此檔案進行測試
    # 在 Colab 環境中，我們是透過 subprocess 來啟動的
    print("INFO: 準備在 http://0.0.0.0:8000 上啟動 Uvicorn 伺服器。")
    
    # 設定環境變數以便在本機測試時也能正常工作
    if not os.getenv('PHOENIX_HEART_ROOT'):
        os.environ['PHOENIX_HEART_ROOT'] = os.getcwd()

    uvicorn.run(app, host="0.0.0.0", port=8000, log_config=None)
