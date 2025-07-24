# -*- coding: utf-8 -*-
import uuid
from fastapi import APIRouter, HTTPException, UploadFile, File

# 導入此 App 的業務邏輯
from . import logic

# --- App 資訊 ---
# 這個字典將被主應用程序讀取，用於在前端顯示
app_info = {
    "id": "transcriber",
    "name": "錄音轉寫服務 (模擬)",
    "icon": "mic",
    "description": "上傳音訊檔案，非同步模擬轉寫任務。",
    "version": "1.0"
}

# --- API 路由器 ---
# 所有此 App 的路由都在這裡定義
router = APIRouter(
    prefix="/api/transcriber",  # 給這個 App 的所有路由加上前綴
    tags=["Transcriber App"],    # 在 API 文檔中分組
)

@router.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    """
    接收上傳的音訊檔案，並創建一個模擬的轉寫任務。
    """
    try:
        task_id = str(uuid.uuid4())
        # 模擬將任務交給背景工作者處理
        result = await logic.create_transcription_task(task_id, file.filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"檔案上傳或任務創建失敗: {str(e)}")

@router.get("/status/{task_id}")
async def get_transcription_status(task_id: str):
    """
    根據任務 ID 查詢模擬的轉寫狀態。
    """
    result = await logic.get_task_status(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail="任務 ID 不存在。")
    return result
