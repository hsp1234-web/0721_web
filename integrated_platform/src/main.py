import sys
import uuid
import asyncio
print(sys.path)
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
import os
from pathlib import Path
from .log_manager import LogManager

# --- 全域設定 ---
LOG_DB_PATH = Path(__file__).parent.parent.parent / "logs.sqlite"
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

from .services import app_service

from fastapi import UploadFile, File, BackgroundTasks
import shutil

@app.get("/api/apps")
async def get_applications():
    log_manager.log("DEBUG", "正在查詢可用的應用程式列表。")
    apps_list = app_service.get_applications()
    log_manager.log("INFO", f"成功返回 {len(apps_list)} 個應用程式。")
    return apps_list

async def process_transcription(job_id: str, file_path: Path):
    """
    一個模擬的背景任務，用來處理轉寫。
    """
    log_manager.log("INFO", f"[{job_id}] 開始處理轉寫...")
    # 模擬長時間運行的任務
    await asyncio.sleep(10)
    # 模擬轉寫結果
    TRANSCRIPTION_JOBS[job_id]["status"] = "completed"
    TRANSCRIPTION_JOBS[job_id]["result"] = "這是模擬的轉寫結果。"
    log_manager.log("INFO", f"[{job_id}] 轉寫完成。")

@app.post("/api/transcribe/upload", status_code=202)
async def upload_audio_for_transcription(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...)
):
    job_id = str(uuid.uuid4())
    file_path = UPLOAD_DIR / f"{job_id}_{audio_file.filename}"

    # 保存上傳的檔案
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(audio_file.file, buffer)

    # 建立工作狀態
    TRANSCRIPTION_JOBS[job_id] = {
        "status": "processing",
        "filename": audio_file.filename,
        "result": None
    }

    # 在背景執行轉寫任務
    background_tasks.add_task(process_transcription, job_id, file_path)
    log_manager.log("INFO", f"已接受轉寫工作 [{job_id}]，檔案為 {audio_file.filename}。")

    return {"job_id": job_id, "message": "檔案已接受並正在處理中。"}

@app.get("/api/transcribe/status/{job_id}")
async def get_transcription_status(job_id: str):
    """
    查詢轉寫工作的狀態。
    """
    job = TRANSCRIPTION_JOBS.get(job_id)
    if not job:
        return {"error": "找不到指定的工作 ID。"}, 404
    return job
