from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
import os
import time
from pathlib import Path
from src.log_manager import LogManager

# --- 全域日誌管理器 ---
# 專案根目錄的相對路徑，指向 logs.sqlite
# 在 run.sh 中，我們是從 `integrated_platform` 目錄下啟動 uvicorn，
# 所以資料庫路徑應該相對於該目錄。
LOG_DB_PATH = Path("../logs.sqlite")
log_manager = LogManager(LOG_DB_PATH)

app = FastAPI(title="整合型應用平台")

current_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(current_dir, "static")

@app.on_event("startup")
async def startup_event():
    """應用啟動時記錄一條日誌。"""
    log_manager.log("INFO", "伺服器應用已啟動。")

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """中介軟體，記錄所有傳入的 HTTP 請求。"""
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

@app.post("/api/transcribe/upload")
async def upload_audio_for_transcription(audio_file: UploadFile = File(...)):
    log_manager.log("INFO", f"收到檔案上傳請求: {audio_file.filename} ({audio_file.content_type})")
    time.sleep(1) # 模擬處理延遲
    transcription_result = f"這是一段針對 '{audio_file.filename}' 的模擬語音轉寫結果。實際的 AI 模型尚未整合。"
    log_manager.log("INFO", f"檔案 '{audio_file.filename}' 的轉寫處理完成。")
    return {
        "filename": audio_file.filename,
        "content_type": audio_file.content_type,
        "transcription": transcription_result
    }
