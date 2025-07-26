# -*- coding: utf-8 -*-
"""
基於 aiosqlite 的非同步任務佇列.
"""
import aiosqlite
from typing import Optional

# 調整導入路徑
from .core import BaseConfig, get_logger

logger = get_logger(__name__)


async def add_task_to_queue(task_id: str, config: BaseConfig) -> None:
    """
    將一個新任務的 ID 加入到佇列中.
    """
    try:
        async with aiosqlite.connect(config.DATABASE_FILE) as db:
            await db.execute(
                "UPDATE transcription_tasks SET status = 'pending' WHERE id = ?",
                (task_id,),
            )
            await db.commit()
            logger.info("任務 %s 已成功加入佇列.", task_id)
    except aiosqlite.Error as e:
        logger.exception("將任務 %s 加入佇列時發生資料庫錯誤: %s", task_id, e)
        raise


async def get_task_from_queue(config: BaseConfig) -> Optional[str]:
    """
    從佇列中獲取一個待處理的任務.
    """
    try:
        async with aiosqlite.connect(config.DATABASE_FILE) as db:
            async with db.execute(
                "SELECT id FROM transcription_tasks WHERE status = 'pending' LIMIT 1"
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    task_id = row[0]
                    await db.execute(
                        "UPDATE transcription_tasks SET status = 'processing' WHERE id = ?",
                        (task_id,),
                    )
                    await db.commit()
                    logger.info("從佇列中領取任務 %s.", task_id)
                    return task_id
            return None
    except aiosqlite.Error as e:
        logger.exception("從佇列獲取任務時發生資料庫錯誤: %s", e)
        return None


async def update_task_status(
    task_id: str,
    status: str,
    config: BaseConfig,
    result_text: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """
    更新任務的狀態、結果或錯誤訊息.
    """
    try:
        async with aiosqlite.connect(config.DATABASE_FILE) as db:
            await db.execute(
                """
                UPDATE transcription_tasks
                SET status = ?, result_text = ?, error_message = ?
                WHERE id = ?
                """,
                (status, result_text, error_message, task_id),
            )
            await db.commit()
            logger.info("任務 %s 的狀態已更新為 %s.", task_id, status)
    except aiosqlite.Error as e:
        logger.exception("更新任務 %s 狀態時發生資料庫錯誤: %s", task_id, e)
        raise
