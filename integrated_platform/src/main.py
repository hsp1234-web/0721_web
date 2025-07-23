import sys
print(sys.path)
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
from .log_manager import LogManager

# --- 全域設定 ---
LOG_DB_PATH = Path("../logs.sqlite")
log_manager = LogManager(LOG_DB_PATH)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
TRANSCRIPTION_JOBS = {}

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    log_manager.log("INFO", "伺服器應用已啟動。")
    yield
    log_manager.log("INFO", "伺服器應用已關閉。")

app = FastAPI(title="整合型應用平台", lifespan=lifespan)

current_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(current_dir, "static")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    log_manager.log("INFO", f"收到請求: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file_path = os.path.join(static_path, "index.html")
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            log_manager.log("INFO", "成功提供前端靜態檔案 (index.html)。")
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        log_manager.log("ERROR", "找不到前端檔案 (index.html)。")
        return HTMLResponse(content="<h1>錯誤：找不到前端檔案 (index.html)</h1>", status_code=404)

@app.get("/api/apps")
async def get_applications():
    log_manager.log("DEBUG", "正在查詢可用的應用程式列表。")
    apps_list = [
        {"id": "transcribe", "name": "錄音轉寫服務", "icon": "mic", "description": "上傳音訊檔案，自動轉換為文字稿。"},
        {"id": "quant", "name": "量化研究框架", "icon": "bar-chart-3", "description": "執行金融策略回測與數據分析。"},
    ]
    log_manager.log("INFO", f"成功返回 {len(apps_list)} 個應用程式。")
    return apps_list

# --- 應用程式啟動 ---
if __name__ == "__main__":
    import uvicorn
    # 使用 uvicorn 來啟動應用程式
    # host="0.0.0.0" 讓服務可以從外部網路存取
    # port=8000 是常用的開發埠號
    # reload=True 可以在程式碼變更時自動重啟伺服器，方便開發
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
