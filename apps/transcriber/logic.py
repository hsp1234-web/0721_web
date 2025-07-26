# 繁體中文: apps/transcriber/logic.py - 語音轉錄核心邏輯封裝

import uuid
import aiofiles
import aiosqlite
from pathlib import Path
from typing import Any, Dict, Optional

from fastapi import UploadFile, HTTPException

# 調整導入路徑
from .core import BaseConfig, get_logger
from .queues import add_task_to_queue

logger = get_logger(__name__)


async def submit_transcription_task(file: UploadFile, config: BaseConfig) -> Dict[str, str]:
    """
    處理檔案上傳，儲存檔案，並在資料庫中創建一個新的轉錄任務。

    Args:
        file (UploadFile): 從 FastAPI 端點接收的上傳檔案。
        config (BaseConfig): 當前的應用設定。

    Returns:
        Dict[str, str]: 包含新任務 ID 的字典。

    Raises:
        HTTPException: 如果檔案或資料庫操作失敗。
    """
    task_id = str(uuid.uuid4())

    # 使用 pathlib 確保路徑操作的穩健性
    filename = file.filename if file.filename else "unknown_file"
    filepath = config.UPLOAD_DIR / f"{task_id}_{filename}"

    try:
        # 確保上傳目錄存在
        config.UPLOAD_DIR.mkdir(exist_ok=True)

        # 非同步寫入檔案
        async with aiofiles.open(filepath, "wb") as out_file:
            while content := await file.read(1024 * 1024):  # 1MB 區塊
                await out_file.write(content)
        logger.info("檔案 '%s' 已上傳至 '%s'", filename, filepath)

        # 在資料庫中記錄任務
        async with aiosqlite.connect(config.DATABASE_FILE) as db:
            await db.execute(
                "INSERT INTO transcription_tasks (id, original_filepath) VALUES (?, ?)",
                (task_id, str(filepath)),
            )
            await db.commit()

        # 將任務加入處理佇列
        await add_task_to_queue(task_id, config)
        logger.info("任務已在資料庫中創建，ID: %s", task_id)

    except IOError as e:
        logger.exception("檔案操作失敗: %s", e)
        raise HTTPException(status_code=500, detail="檔案操作失敗。") from e
    except aiosqlite.Error as e:
        logger.exception("資料庫操作失敗: %s", e)
        raise HTTPException(status_code=500, detail="資料庫操作失敗。") from e

    return {"task_id": task_id}


async def get_task_status(task_id: str, config: BaseConfig) -> Optional[Dict[str, Any]]:
    """
    根據任務 ID 查詢並返回任務的狀態和結果。

    Args:
        task_id (str): 要查詢的任務 ID。
        config (BaseConfig): 當前的應用設定。

    Returns:
        Optional[Dict[str, Any]]: 如果找到任務，返回包含任務詳情的字典，否則返回 None。

    Raises:
        HTTPException: 如果資料庫查詢失敗。
    """
    try:
        async with aiosqlite.connect(config.DATABASE_FILE) as db:
            db.row_factory = aiosqlite.Row  # 以字典形式返回結果
            async with db.execute(
                "SELECT * FROM transcription_tasks WHERE id = ?", (task_id,)
            ) as cursor:
                task_data = await cursor.fetchone()

        if task_data:
            return dict(task_data)
        return None

    except aiosqlite.Error as e:
        logger.exception("查詢任務狀態時出錯 (ID: %s): %s", task_id, e)
        raise HTTPException(status_code=500, detail="查詢狀態時出錯。") from e
