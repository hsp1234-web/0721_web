# -*- coding: utf-8 -*-
"""
語音轉寫 App (Transcriber) - FastAPI 伺服器入口
"""
import os

# 這裡我們需要能夠導入同目錄下的 logic 模組
# 在微服務架構中，每個 App 都是一個獨立的執行單元
# 所以我們需要確保 Python 的導入路徑是正確的
import uvicorn
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

# 在新的 src 架構下，不再需要手動修改 sys.path，我們將使用相對導入。
from src.transcriber import logic

# 建立 FastAPI 應用實例
app = FastAPI(
    title="鳳凰之心 - 語音轉寫服務 (Transcriber App)",
    description="一個獨立的微服務，負責接收音訊檔案並進行語音轉寫。",
    version="1.0.0",
)

from fastapi import Depends

...

@app.post("/upload", summary="上傳音訊檔案以進行轉寫")
async def upload_audio(
    file: UploadFile = File(...),
    process_audio_file: callable = Depends(logic.process_audio_file)
):
    """
    接收使用者上傳的音訊檔案，並啟動轉寫任務。
    """

    if not file:
        raise HTTPException(status_code=400, detail="沒有提供檔案。")

    task_id = process_audio_file(file)

    return JSONResponse(
        status_code=202,
        content={"message": "檔案已成功上傳並開始處理。", "task_id": task_id}
    )

@app.get("/status/{task_id}", summary="查詢轉寫任務的狀態與結果")
async def get_transcription_status(
    task_id: str,
    get_task_status: callable = Depends(logic.get_task_status)
):
    """
    根據任務 ID 查詢轉寫任務的狀態。
    """
    status_info = get_task_status(task_id)
    if status_info.get("status") == "not_found":
        raise HTTPException(status_code=404, detail=f"找不到任務 ID: {task_id}")

    return JSONResponse(content=status_info)

@app.get("/", summary="服務健康檢查")
def read_root():
    """
    根路由，用於簡單的服務健康檢查。
    """
    return {"status": "ok", "service": "鳳凰之心 - 語音轉寫服務"}

@app.get("/", summary="服務健康檢查")
def read_root():
    """
    根路由，用於簡單的服務健康檢查。
    """
    return {"status": "ok", "service": "鳳凰之心 - 語音轉寫服務"}

@app.get("/", summary="服務健康檢查")
def read_root():
    """
    根路由，用於簡單的服務健康檢查。
    """
    return {"status": "ok", "service": "鳳凰之心 - 語音轉寫服務"}

@app.get("/health", summary="服務健康檢查")
def health_check():
    """
    一個簡單的健康檢查端點，用於確認服務是否正在運行。
    """
    return {"status": "ok", "message": "語音轉寫服務運行中"}

def start():
    """
    使用 uvicorn 啟動伺服器。
    這個函式將被 launch.py 呼叫。
    我們從環境變數讀取埠號，以便 launch.py 可以為每個 App 分配不同埠號。
    """
    port = int(os.environ.get("PORT", 8002)) # 預設為 8002
    # The app is passed as a string 'src.transcriber.main:app' to uvicorn
    # to ensure consistent behavior between test and production.
    uvicorn.run("src.transcriber.main:app", host="0.0.0.0", port=port, log_level="info", reload=True)

if __name__ == "__main__":
    # 這使得我們可以獨立運行這個 App 進行測試
    # 在終端機中執行 `python -m src.transcriber.main`
    print("正在以獨立模式啟動語音轉寫伺服器...")
    start()
