"""真實轉寫工人模組"""
import asyncio
import multiprocessing as mp
import time
from typing import Any, Optional

from faster_whisper import WhisperModel
import aiosqlite

from prometheus.core.logging.log_manager import LogManager
from prometheus.transcriber.core import DATABASE_FILE
from prometheus.transcriber.core.hardware import get_best_hardware_config

# --- 日誌記錄器設定 ---
log_manager = LogManager(log_file="transcriber_worker.log")
logger = log_manager.get_logger(__name__)


async def process_single_task(task_id: str) -> None:
    """
    處理一個指定的轉寫任務。

    Args:
        task_id (str): 要處理的任務 ID。
    """
    logger.info("開始處理任務: %s", task_id)
    audio_path = None

    try:
        # 1. 更新任務狀態為 'processing'
        await update_task_status_in_db(task_id, "processing")

        # 2. 從資料庫獲取音檔路徑
        async with aiosqlite.connect(DATABASE_FILE) as db:
            async with db.execute(
                "SELECT original_filepath FROM transcription_tasks WHERE id = ?",
                (task_id,),
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    logger.error("在資料庫中找不到任務 %s 的檔案路徑。", task_id)
                    await update_task_status_in_db(task_id, "failed", error_message="找不到檔案路徑")
                    return
                audio_path = row[0]

        # 3. 執行轉寫
        hardware_config = get_best_hardware_config()
        logger.info("使用硬體設定: %s", hardware_config)
        model = WhisperModel(
            "tiny",  # 暫時使用 tiny 模型以利測試
            device=hardware_config["device"],
            compute_type=hardware_config["compute_type"],
        )
        segments, _info = model.transcribe(audio_path, beam_size=5)
        full_transcript = "".join(segment.text for segment in segments)
        logger.info("任務 %s: 轉寫完成。", task_id)

        # 4. 更新最終結果
        await update_task_status_in_db(
            task_id, "completed", result_text=full_transcript.strip()
        )
        logger.info("任務 %s 狀態更新為: completed", task_id)

    except Exception as e:
        logger.exception("處理任務 %s 過程中發生錯誤", task_id)
        await update_task_status_in_db(task_id, "failed", error_message=str(e))
        logger.info("任務 %s 狀態更新為: failed", task_id)


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


def transcriber_worker_process(
    log_queue: Optional[mp.Queue],
    task_queue: mp.Queue,
    result_queue: Optional[mp.Queue],
    config: Optional[dict[str, Any]],
) -> None:
    """
    轉寫工人行程的主函數。

    它會持續從任務佇列中獲取任務 ID，並呼叫 `process_single_task` 進行處理。
    """
    # 此處的 log_queue, result_queue, config 暫未使用，但保留簽名以符合架構
    logger.info("真實轉寫工人行程已啟動 (PID: %s)", mp.current_process().pid)

    async def main_loop() -> None:
        while True:
            try:
                # 從佇列中獲取任務，如果佇列為空，會阻塞等待
                task_id = task_queue.get()
                if task_id is None:
                    logger.info("收到結束信號，工人行程即將關閉。")
                    break
                await process_single_task(task_id)
            except (KeyboardInterrupt, SystemExit):
                logger.info("工人行程收到中斷信號，正在關閉。")
                break
            except Exception:
                logger.exception("工人在主循環中發生嚴重錯誤，將在10秒後重試。")
                await asyncio.sleep(10)

    # 為了能在同步函數中運行異步循環
    asyncio.run(main_loop())


if __name__ == "__main__":
    # 這部分保留用於獨立測試
    # 為了直接運行, 需要一個模擬的佇列
    class MockQueue:
        """模擬佇列."""

        def put(self, *args: Any, **kwargs: Any) -> None:
            """模擬 put."""
            pass

    transcriber_worker_process(MockQueue(), mp.Queue(), mp.Queue(), {})
