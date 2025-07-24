from typing import Any, Dict

from fastapi import APIRouter, File, HTTPException, UploadFile

from . import logic

router = APIRouter()


@router.get("/", summary="服務健康檢查")
def transcriber_root() -> Dict[str, str]:
    """提供一個簡單的 API 端點，用於確認 Transcriber 服務是否正常運行。"""
    return {"message": "這裡是語音轉錄 (Transcriber) 服務，已準備好接收上傳。"}


@router.post("/upload", summary="上傳音訊檔案進行轉錄")
def upload_and_transcribe(file: UploadFile = File(...)) -> Dict[str, Any]:
    """上傳一個音訊檔案，系統將對其進行模擬的語音轉錄。

    - **注意**: 首次調用此 API 時，後端會需要幾秒鐘來加載 AI 模型，
      因此第一次的回應時間會比較長。後續的調用將會非常快。
    """
    if not file:
        raise HTTPException(status_code=400, detail="沒有提供上傳檔案。")

    if not file.content_type or not file.content_type.startswith("audio/"):
        raise HTTPException(
            status_code=415,
            detail=f"不支援的檔案類型: '{file.content_type}'。請上傳音訊檔案。",
        )

    try:
        result = logic.transcribe_audio(file)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"處理檔案時發生內部錯誤: {e}")
