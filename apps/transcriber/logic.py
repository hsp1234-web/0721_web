# -*- coding: utf-8 -*-
import asyncio
import random
from typing import Dict, Any

# --- 模擬資料庫 ---
# 在真實應用中，這可能是一個 Redis, aio-pika, 或其他資料庫的連接
MOCK_TASK_DB: Dict[str, Dict[str, Any]] = {}

async def create_transcription_task(task_id: str, filename: str) -> Dict[str, str]:
    """
    模擬創建一個轉寫任務。
    """
    MOCK_TASK_DB[task_id] = {
        "status": "pending",
        "filename": filename,
        "result": None,
        "error": None
    }
    # 模擬背景工作
    asyncio.create_task(run_mock_transcription(task_id))
    return {"task_id": task_id, "message": "檔案已上傳，轉寫任務已啟動。"}

async def get_task_status(task_id: str) -> Dict[str, Any] | None:
    """
    模擬獲取任務狀態。
    """
    return MOCK_TASK_DB.get(task_id)

async def run_mock_transcription(task_id: str):
    """
    一個模擬的背景轉寫任務。
    """
    await asyncio.sleep(5) # 模擬 I/O 綁定或網路延遲

    task = MOCK_TASK_DB[task_id]
    task["status"] = "processing"

    await asyncio.sleep(random.uniform(5, 15)) # 模擬 CPU 密集型工作

    if "error" in task["filename"].lower():
        task["status"] = "failed"
        task["error"] = "檔案名包含 'error'，觸發模擬失敗。"
    else:
        task["status"] = "completed"
        task["result"] = f"這是 '{task['filename']}' 的模擬轉寫結果。"

    print(f"背景任務 {task_id} 完成，狀態: {task['status']}")
