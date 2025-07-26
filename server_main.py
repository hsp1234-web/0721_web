#!

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os

# 建立 FastAPI 應用程式實例
app = FastAPI(
    title="鳳凰之心-後端引擎",
    description="提供儀表板介面與核心 API 服務",
    version="1.0.0"
)

# 取得目前檔案所在的絕對路徑
# 這能確保無論從哪裡執行腳本，都能正確找到 templates 和 static 資料夾
BASE_DIR = Path(__file__).resolve().parent

# --- 關鍵修正 ---
# 1. 設定模板引擎，並告訴它去哪裡找 HTML 檔案 (在 'templates' 資料夾中)
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# 2. 掛載靜態檔案目錄 (可選，但為良好實踐)
# 如果您的 dashboard.html 有引用外部的 CSS 或 JS 檔案，就需要這行
# 假設您的靜態檔案放在 'static' 資料夾中
static_path = BASE_DIR / "static"
if static_path.is_dir():
    app.mount("/static", StaticFiles(directory=static_path), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    根路徑端點。
    當使用者訪問網站首頁時，這個函式會被觸發。
    它會回傳渲染後的 dashboard.html 頁面。
    """
    # 使用模板引擎來渲染 HTML 檔案
    # "request": request 是 FastAPI 模板渲染的必要參數
    return templates.TemplateResponse(
        "dashboard.html", {"request": request}
    )

# --- WebSocket 和其他 API 端點可以加在這裡 ---
# 例如: @app.websocket("/ws/logs") ...

if __name__ == "__main__":
    # 讓這個腳本也能夠被直接執行 (python server_main.py)
    # 從環境變數讀取埠號，若無則使用預設值 8000
    port = int(os.environ.get("FASTAPI_PORT", 8000))
    
    # uvicorn.run 會啟動伺服器
    # host="0.0.0.0" 表示允許來自任何網路介面的連線
    # reload=True 會在程式碼變更時自動重啟伺服器，方便開發
    uvicorn.run("server_main:app", host="0.0.0.0", port=port, reload=True)
