# apps/transcriber/logic.py
import uuid
import asyncio
import multiprocessing
from pathlib import Path
from .queues import (
    get_task_queue,
    get_result_queue,
    get_task_store,
    get_result_store
)
from .transcriber_worker import run_transcription_worker_process

# --- 變數 ---
# 使用 multiprocessing.Manager 來在不同進程間共享狀態
# 這對於追蹤任務狀態至關重要
_manager = multiprocessing.Manager()
_task_store = get_task_store(_manager)
_result_store = get_result_store(_manager)

# --- 背景工作者管理 ---
worker_process = None

def start_worker():
    """在背景啟動轉錄工作者進程。"""
    global worker_process
    if worker_process is None or not worker_process.is_alive():
        print("正在啟動語音轉錄背景工作者...")
        task_queue = get_task_queue()
        result_queue = get_result_queue()
        # 注意：我們傳遞的是由 Manager 管理的共享字典
        worker_process = multiprocessing.Process(
            target=run_transcription_worker_process,
            args=(task_queue, result_queue, _task_store, _result_store)
        )
        worker_process.start()
        print(f"背景工作者已啟動，PID: {worker_process.pid}")

def stop_worker():
    """停止轉錄工作者進程。"""
    global worker_process
    if worker_process and worker_process.is_alive():
        print("正在停止語音轉錄背景工作者...")
        worker_process.terminate()
        worker_process.join()
        print("背景工作者已停止。")
    _manager.shutdown()

# --- 任務管理 ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def create_transcription_task(file) -> str:
    """
    創建一個新的轉錄任務。

    Args:
        file: 上傳的檔案物件 (來自 FastAPI)。

    Returns:
        新任務的 ID。
    """
    task_id = str(uuid.uuid4())
    # 安全地儲存上傳的檔案
    file_path = UPLOAD_DIR / f"{task_id}_{file.filename}"

    with open(file_path, "wb") as buffer:
        buffer.write(await file.read())

    task_queue = get_task_queue()
    task_data = {"task_id": task_id, "file_path": str(file_path)}

    # 將任務加入佇列
    task_queue.put(task_data)

    # 在共享的任務儲存中記錄任務狀態
    _task_store[task_id] = {"status": "pending", "file_path": str(file_path)}

    print(f"已創建轉錄任務: {task_id}")
    return task_id

def get_task_status(task_id: str) -> dict:
    """
    查詢轉錄任務的狀態和結果。

    Args:
        task_id: 要查詢的任務 ID。

    Returns:
        一個包含任務狀態和結果的字典。
    """
    # 檢查結果儲存區
    if task_id in _result_store:
        return _result_store[task_id]

    # 如果還沒有結果，檢查原始任務儲存區
    if task_id in _task_store:
        return _task_store[task_id]

    return {"status": "not_found"}
