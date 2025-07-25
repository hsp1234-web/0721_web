import asyncio
import json
import logging
from core import manager

# --- WebSocket 日誌處理程序 ---
class WebSocketLogHandler(logging.Handler):
    """一個自訂的日誌處理程序，可將日誌轉發到 WebSocket 連線。"""

    def emit(self, record: logging.LogRecord) -> None:
        """將日誌記錄格式化並透過 WebSocket 管理器廣播。"""
        try:
            # 將 LogRecord 轉換為字典
            log_data = {
                "timestamp": record.created,
                "level": record.levelname,
                "message": self.format(record),
            }

            # 根據附錄 A 協議構建訊息
            protocol_message = {"event_type": "LOG_MESSAGE", "payload": log_data}

            # 廣播 JSON 訊息
            # 我們需要獲取或創建一個事件循環在當前執行緒
            try:
                loop = asyncio.get_running_loop()
            except RuntimeError:  # 'RuntimeError: There is no current event loop...'
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            loop.run_until_complete(manager.broadcast(json.dumps(protocol_message)))
        except Exception:
            # 在日誌處理程序中應避免引發異常
            pass

def setup_logging() -> None:
    """設定全域日誌記錄，將日誌同時輸出到控制台和 WebSocket。"""
    websocket_handler = WebSocketLogHandler()
    websocket_handler.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
    )
    websocket_handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除任何可能已存在的處理程序，以避免日誌重複
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(websocket_handler)

    # 添加控制台輸出，以便在伺服器端也能看到日誌
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    logging.info("日誌系統已初始化，WebSocket 處理程序已掛載。")
