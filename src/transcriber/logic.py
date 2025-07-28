# -*- coding: utf-8 -*-
"""
語音轉寫 App 的核心業務邏輯
"""
import os
import shutil
import uuid
from pathlib import Path

from fastapi import UploadFile

# --- 嘗試導入大型依賴 ---
try:
    from faster_whisper import WhisperModel
    _FASTER_WHISPER_AVAILABLE = True
except ImportError:
    _FASTER_WHISPER_AVAILABLE = False

# --- 全局變數與設定 ---
# 在真實模式下，我們會初始化一個模型
# 注意：這在生產環境中應該有更複雜的模型管理
MODEL_SIZE = "tiny" # 使用一個小模型以加快速度
_model = None

if _FASTER_WHISPER_AVAILABLE:
    # 這裡的下載只會在第一次執行時發生
    # 在 launch.py 啟動時，這會被觸發
    try:
        _model = WhisperModel(MODEL_SIZE, device="cpu", compute_type="int8")
    except Exception as e:
        print(f"警告：無法初始化 Whisper 模型: {e}")
        _model = None


UPLOAD_DIRECTORY = Path("transcriber_uploads")
UPLOAD_DIRECTORY.mkdir(exist_ok=True)

# 模擬一個任務資料庫
tasks = {}

def process_audio_file(file: UploadFile) -> str:
    """
    處理上傳的音訊檔案，並啟動一個轉寫任務。

    - 如果處於真實模式 (`faster-whisper` 可用)，則執行轉寫。
    - 如果處於模擬模式，則返回一個模擬結果。
    """
    task_id = str(uuid.uuid4())
    safe_filename = Path(file.filename).name
    file_path = UPLOAD_DIRECTORY / f"{task_id}_{safe_filename}"

    try:
        # 保存上傳的檔案
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        file.file.close()

        # 根據是否能使用模型來決定行為
        # os.environ.get("APP_MOCK_MODE") == "true" 是由我們的測試腳本設定的
        if not _FASTER_WHISPER_AVAILABLE or os.environ.get("APP_MOCK_MODE") == "true" or _model is None:
            # --- 模擬模式 ---
            tasks[task_id] = {
                "status": "completed",
                "original_filename": safe_filename,
                "result": f"這是 '{safe_filename}' 的模擬轉寫結果。",
                "mode": "mock"
            }
        else:
            # --- 真實模式 ---
            tasks[task_id] = {
                "status": "processing",
                "original_filename": safe_filename,
                "result": None,
                "mode": "real"
            }
            # 實際執行轉寫
            segments, _ = _model.transcribe(str(file_path), beam_size=5)
            transcription = " ".join([segment.text for segment in segments])

            tasks[task_id]["status"] = "completed"
            tasks[task_id]["result"] = transcription

        return task_id
    except Exception as e:
        # 如果轉寫過程出錯，也記錄下來
        tasks[task_id] = {"status": "error", "error_message": str(e)}
        return task_id


def get_task_status(task_id: str) -> dict:
    """
    根據任務 ID 獲取轉寫任務的狀態和結果。
    """
    return tasks.get(task_id, {"status": "not_found"})
