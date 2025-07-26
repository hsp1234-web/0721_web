"""轉錄工人模組."""
import asyncio
import time
import aiosqlite
from faster_whisper import WhisperModel

# 調整導入路徑
from .core import get_logger, get_config, BaseConfig
from .core.hardware import get_best_hardware_config
from .queues import get_task_from_queue, update_task_status

# 在模組級別獲取日誌記錄器
# 注意：在多行程環境中，日誌佇列的配置需要在啟動時完成
logger = get_logger("轉錄工人")

async def process_single_task(config: BaseConfig) -> None:
    """處理單個轉錄任務."""
    task_id = await get_task_from_queue(config)

    if task_id:
        logger.info("找到待處理任務: %s", task_id)

        try:
            # 執行轉錄
            hardware_config = get_best_hardware_config()
            model = WhisperModel(
                config.MODEL_SIZE,
                device=hardware_config["device"],
                compute_type=hardware_config["compute_type"],
            )

            async with aiosqlite.connect(config.DATABASE_FILE) as db:
                async with db.execute(
                    "SELECT original_filepath FROM transcription_tasks WHERE id = ?",
                    (task_id,),
                ) as cursor:
                    row = await cursor.fetchone()
                    if not row:
                        logger.error("在資料庫中找不到任務 %s 的檔案路徑。", task_id)
                        return
                    audio_path = row[0]

            segments, _info = model.transcribe(audio_path, beam_size=config.BEAM_SIZE)
            full_transcript = "".join(segment.text for segment in segments)
            logger.info("任務 %s: 轉錄完成.", task_id)

            # 更新最終結果
            await update_task_status(
                task_id, "completed", config, result_text=full_transcript.strip()
            )
            logger.info("任務 %s 狀態更新為: completed", task_id)

        except Exception as e:
            logger.exception("轉錄任務 %s 過程中發生錯誤", task_id)
            await update_task_status(task_id, "failed", config, error_message=str(e))
            logger.info("任務 %s 狀態更新為: failed", task_id)


def worker_main_loop(config: BaseConfig) -> None:
    """工人的主循環，現在是一個獨立的同步函數，內部運行 asyncio 事件循環。"""
    logger.info(f"轉錄工人已使用 '{config.PROFILE_NAME}' 配置啟動")

    async def main() -> None:
        while True:
            try:
                await process_single_task(config)
                await asyncio.sleep(5)  # 每5秒檢查一次新任務
            except Exception:
                logger.exception("工人在主循環中發生嚴重錯誤")
                await asyncio.sleep(10)  # 如果發生錯誤, 等待更長時間

    asyncio.run(main())


if __name__ == "__main__":
    # 這部分用於獨立測試工人邏輯
    print("正在以獨立模式啟動轉錄工人...")

    # 使用預設的測試配置
    test_config = get_config("testing")

    # 在獨立運行前，需要確保資料庫已初始化
    # 這是一個簡化的初始化過程
    async def setup_test_db():
        from .core import initialize_database
        await initialize_database(test_config)
        print("測試資料庫已初始化。")

    asyncio.run(setup_test_db())

    print("工人正在運行... 按下 Ctrl+C 以停止。")
    worker_main_loop(test_config)
