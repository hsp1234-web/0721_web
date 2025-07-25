import logging
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

# 嘗試從 core.monitor 導入中央佇列。
# 這樣做可以讓日誌系統與核心系統解耦，即使在沒有佇列的環境下也能獨立運作。
try:
    from core.monitor import SYSTEM_EVENTS_QUEUE
except ImportError:
    SYSTEM_EVENTS_QUEUE = None

class QueueHandler(logging.Handler):
    """
    一個自定義的日誌處理程序，它將日誌記錄放入 asyncio.Queue 中。
    """
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record: logging.LogRecord):
        # 格式化日誌訊息
        log_entry = self.format(record)

        # 建立標準的事件負載 (payload)
        log_payload = {
            "type": "LOG_MESSAGE",
            "timestamp": datetime.fromtimestamp(record.created, tz=ZoneInfo("Asia/Taipei")).isoformat(),
            "data": {
                "level": record.levelname.lower(),
                "message": log_entry,
                "source": record.name,
            }
        }

        # 由於 logging 不是 async-native，我們不能在這裡 await
        # 我們使用 thread-safe 的 put_nowait 方法
        try:
            self.queue.put_nowait(log_payload)
        except Exception as e:
            # 如果佇列已滿或發生其他錯誤，打印到 stderr
            print(f"Failed to queue log message: {e}", file=sys.stderr)


def setup_logger():
    """
    設定全域日誌記錄器。
    它會將日誌同時輸出到控制台和中央事件佇列（如果可用）。
    """
    # 獲取根記錄器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 如果已經有處理程序，就先清除，防止重複設定
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. 設定控制台輸出 (StreamHandler)
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    stream_handler.setFormatter(stream_formatter)
    root_logger.addHandler(stream_handler)

    # 2. 設定中央佇列輸出 (QueueHandler)
    if SYSTEM_EVENTS_QUEUE:
        queue_handler = QueueHandler(SYSTEM_EVENTS_QUEUE)
        # 我們可以為佇列設定更簡潔的格式，因為大部分元數據已經在 payload 中
        queue_formatter = logging.Formatter('%(message)s')
        queue_handler.setFormatter(queue_formatter)
        root_logger.addHandler(queue_handler)
        logging.info("Logger setup with Console and Queue handlers.")
    else:
        logging.info("Logger setup with Console handler only (Queue not available).")

# 在模組導入時自動設定日誌記錄器
setup_logger()

# 使用範例 (如果直接執行此檔案):
async def main_async():
    import asyncio

    if not SYSTEM_EVENTS_QUEUE:
        print("SYSTEM_EVENTS_QUEUE not found. Cannot run this example.")
        return

    # 模擬從佇列讀取日誌
    async def log_reader():
        while True:
            try:
                item = await asyncio.wait_for(SYSTEM_EVENTS_QUEUE.get(), timeout=2.0)
                print(f"--- Received from Queue ---> {item}")
                SYSTEM_EVENTS_QUEUE.task_done()
            except asyncio.TimeoutError:
                print("Queue is empty. Exiting.")
                break

    # 產生一些測試日誌
    logging.info("這是一條資訊日誌。")
    logging.warning("這是一條警告日誌。")
    logging.error("這是一條錯誤日誌。")

    await log_reader()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main_async())
