import sys
print(sys.path)
from fastapi import FastAPI, UploadFile, File, Request, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
import os
from pathlib import Path
import uuid
import aiofiles
from .log_manager import LogManager

# --- 全域設定 ---
LOG_DB_PATH = Path("../logs.sqlite")
log_manager = LogManager(LOG_DB_PATH)
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)
TRANSCRIPTION_JOBS = {}

# --- Whisper 模型加載 ---
def get_model_size():
    return os.environ.get("WHISPER_MODEL_SIZE", "medium")

def load_whisper_model():
    model_size = get_model_size()
    log_manager.log("INFO", f"正在加載 Whisper 模型，尺寸: {model_size}...")
    try:
        model = whisper.load_model(model_size)
        log_manager.log("SUCCESS", f"成功加載 Whisper 模型 ({model_size})。")
        return model
    except Exception as e:
        log_manager.log("CRITICAL", f"加載 Whisper 模型失敗: {e}")
        return None

model = load_whisper_model()

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

def process_transcription(job_id: str, audio_path: str):
    global TRANSCRIPTION_JOBS
    try:
        log_manager.log("INFO", f"工作 {job_id}: 開始轉寫檔案 {audio_path}...")
        TRANSCRIPTION_JOBS[job_id] = {"status": "processing", "result": None}

        if model is None:
            raise RuntimeError("Whisper 模型未能成功加載。")

        result = model.transcribe(audio_path)

        TRANSCRIPTION_JOBS[job_id] = {"status": "completed", "result": result}
        log_manager.log("SUCCESS", f"工作 {job_id}: 轉寫完成。")
    except Exception as e:
        log_manager.log("ERROR", f"工作 {job_id}: 轉寫過程中發生錯誤: {e}")
        TRANSCRIPTION_JOBS[job_id] = {"status": "failed", "error": str(e)}
    finally:
        # 清理上傳的檔案
        if os.path.exists(audio_path):
            os.remove(audio_path)
            log_manager.log("INFO", f"工作 {job_id}: 已清理臨時檔案 {audio_path}。")


@app.post("/api/transcribe/upload")
async def upload_audio_for_transcription(background_tasks: BackgroundTasks, audio_file: UploadFile = File(...)):
    log_manager.log("INFO", f"收到檔案上傳請求: {audio_file.filename} ({audio_file.content_type})")

    job_id = str(uuid.uuid4())
    file_extension = Path(audio_file.filename).suffix
    temp_audio_path = UPLOAD_DIR / f"{job_id}{file_extension}"

    try:
        async with aiofiles.open(temp_audio_path, 'wb') as out_file:
            content = await audio_file.read()
            await out_file.write(content)

        log_manager.log("INFO", f"檔案已暫存至 {temp_audio_path}")

        background_tasks.add_task(process_transcription, job_id, str(temp_audio_path))

        TRANSCRIPTION_JOBS[job_id] = {"status": "queued"}

        return JSONResponse(
            status_code=202,
            content={
                "job_id": job_id,
                "status": "queued",
                "message": "轉寫任務已加入佇列，請稍後查詢結果。"
            }
        )
    except Exception as e:
        log_manager.log("ERROR", f"檔案上傳或任務創建失敗: {e}")
        return JSONResponse(status_code=500, content={"error": "處理檔案時發生內部錯誤。"})


@app.get("/api/transcribe/status/{job_id}")
async def get_transcription_status(job_id: str):
    job = TRANSCRIPTION_JOBS.get(job_id)
    if not job:
        return JSONResponse(status_code=404, content={"error": "找不到指定的任務 ID。"})

    log_manager.log("INFO", f"正在查詢工作 {job_id} 的狀態: {job['status']}")
    return JSONResponse(content=job)
