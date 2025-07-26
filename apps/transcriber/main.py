# apps/transcriber/main.py
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from .logic import create_transcription_task, get_task_status

# 建立一個新的 API 路由器，並為其所有路由設定統一的前綴
router = APIRouter(prefix="/api/transcriber", tags=["語音轉錄"])

@router.post("/upload")
async def upload_audio_file(file: UploadFile = File(...)):
    """
    上傳音檔以進行轉錄。

    接收一個音檔，將其儲存並為其創建一個背景轉錄任務。
    """
    # 限制檔案類型，這是一個好的實踐
    if not file.content_type.startswith("audio/"):
        raise HTTPException(status_code=400, detail="無效的檔案類型，請上傳音檔。")

    try:
        task_id = await create_transcription_task(file)
        return {"message": "任務已成功創建", "task_id": task_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"創建任務時發生錯誤: {e}")

@router.get("/status/{task_id}")
async def get_transcription_status(task_id: str):
    """
    查詢轉錄任務的狀態。

    使用任務 ID 輪詢此端點，以獲取任務的當前狀態和（如果已完成）結果。
    """
    status_info = get_task_status(task_id)

    if status_info["status"] == "not_found":
        raise HTTPException(status_code=404, detail="找不到指定的任務 ID。")

    return status_info
