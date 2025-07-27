import time
from typing import Any, Dict, Optional

from fastapi import UploadFile

# --- 懶加載 (Lazy Loading) 的核心 ---

AI_MODEL: Optional[Dict[str, Any]] = None


def _load_model() -> Dict[str, Any]:
    """一個模擬的、耗時的模型加載函數。

    在真實應用中，這裡會是 `torch.load()` 或類似的操作。
    """
    print("[Transcriber Logic] 開始加載大型 AI 模型... (這會需要幾秒鐘)")
    # 模擬 IO 或計算密集型操作
    time.sleep(5)
    model_data = {"version": "1.0", "load_time": time.time()}
    print(f"[Transcriber Logic] 模型加載完畢！資料: {model_data}")
    return model_data


def get_model() -> Dict[str, Any]:
    """獲取模型的接口。這是實現懶加載的關鍵。"""
    global AI_MODEL
    if AI_MODEL is None:
        AI_MODEL = _load_model()
    return AI_MODEL


# --- 業務邏輯函數 ---


def transcribe_audio(file: UploadFile) -> Dict[str, Any]:
    """處理音訊轉錄的核心業務邏輯。"""
    model = get_model()

    print(
        f"[Transcriber Logic] 正在使用模型 {model['version']} 處理檔案: {file.filename}"
    )
    time.sleep(1)

    content = file.file.read(100)
    transcription_result = (
        f"檔案 '{file.filename}' (大小: {file.size} 字節) 的模擬轉錄結果。"
        f"內容開頭: {content[:50]!r}..."
    )

    print("[Transcriber Logic] 處理完畢。")

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "transcription": transcription_result,
        "model_used": model,
    }
