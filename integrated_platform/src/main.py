from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import os
import time

app = FastAPI(title="整合型應用平台")

current_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(current_dir, "static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file_path = os.path.join(static_path, "index.html")
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>錯誤：找不到前端檔案 (index.html)</h1>", status_code=404)

@app.get("/api/apps")
async def get_applications():
    return [
        {"id": "transcribe", "name": "錄音轉寫服務", "icon": "mic", "description": "上傳音訊檔案，自動轉換為文字稿。"},
        {"id": "quant", "name": "量化研究框架", "icon": "bar-chart-3", "description": "執行金融策略回測與數據分析。"},
    ]

@app.post("/api/transcribe/upload")
async def upload_audio_for_transcription(audio_file: UploadFile = File(...)):
    time.sleep(1) # 模擬處理延遲
    return {
        "filename": audio_file.filename,
        "content_type": audio_file.content_type,
        "transcription": f"這是一段針對 '{audio_file.filename}' 的模擬語音轉寫結果。實際的 AI 模型尚未整合。"
    }
