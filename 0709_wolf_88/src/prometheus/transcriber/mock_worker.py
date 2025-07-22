"""模擬轉寫工人模組"""
import asyncio
import multiprocessing as mp
import time
from typing import Any, Optional

import aiosqlite

from prometheus.core.logging.log_manager import LogManager
from prometheus.transcriber.core import DATABASE_FILE

# --- 日誌記錄器設定 ---
log_manager = LogManager(log_file="transcriber_mock_worker.log")
logger = log_manager.get_logger(__name__)


async def simulate_task_processing(task_id: str) -> None:
    """
    模擬處理一個指定的轉寫任務。

    Args:
        task_id (str): 要模擬處理的任務 ID。
    """
    logger.info("模擬處理任務: %s", task_id)

    try:
        # 1. 模擬更新任務狀態為 'processing'
        await update_task_status_in_db(task_id, "processing")
        logger.info("任務 %s: 狀態更新為 -> processing", task_id)
        await asyncio.sleep(0.5)  # 模擬處理延遲

        # 2. 模擬轉寫完成
        mock_transcript = f"這是任務 {task_id} 的模擬轉寫結果。"
        logger.info("任務 %s: 模擬轉寫完成。", task_id)
        await asyncio.sleep(0.5)

        # 3. 更新最終結果
        await update_task_status_in_db(
            task_id, "completed", result_text=mock_transcript
        )
        logger.info("任務 %s: 狀態更新為 -> completed", task_id)

    except Exception as e:
        logger.exception("模擬處理任務 %s 過程中發生錯誤", task_id)
        await update_task_status_in_db(task_id, "failed", error_message=str(e))
        logger.info("任務 %s: 狀態更新為 -> failed", task_id)


async def update_task_status_in_db(
    task_id: str,
    status: str,
    result_text: Optional[str] = None,
    error_message: Optional[str] = None,
) -> None:
    """在資料庫中更新任務的狀態、結果或錯誤訊息。"""
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                """
                UPDATE transcription_tasks
                SET status = ?, result_text = ?, error_message = ?
                WHERE id = ?
                """,
                (status, result_text, error_message, task_id),
            )
            await db.commit()
    except aiosqlite.Error as e:
        logger.exception("更新任務 %s 狀態時發生資料庫錯誤", task_id)


def mock_worker_process(
    log_queue: Optional[mp.Queue],
    task_queue: mp.Queue,
    result_queue: Optional[mp.Queue],
    config: Optional[dict[str, Any]],
) -> None:
    """
    模擬轉寫工人行程的主函數。

    它會持續從任務佇列中獲取任務 ID，並呼叫 `simulate_task_processing` 進行模擬處理。
    """
    logger.info("模擬轉寫工人行程已啟動 (PID: %s)", mp.current_process().pid)

    async def main_loop() -> None:
        while True:
            try:
                task_id = task_queue.get()
                if task_id is None:
                    logger.info("收到結束信號，模擬工人行程即將關閉。")
                    break
                await simulate_task_processing(task_id)
            except (KeyboardInterrupt, SystemExit):
                logger.info("模擬工人行程收到中斷信號，正在關閉。")
                break
            except Exception:
                logger.exception("模擬工人在主循環中發生嚴重錯誤，將在10秒後重試。")
                await asyncio.sleep(10)

    asyncio.run(main_loop())
