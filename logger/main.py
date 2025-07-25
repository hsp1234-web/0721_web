import logging
import os
import asyncio
from logging.handlers import RotatingFileHandler
from core.config import settings
from datetime import datetime
import pytz

# 這個全域變數用來儲存 WebSocket 管理器的實例
websocket_manager = None

def set_websocket_manager(manager):
    """設定 WebSocket 管理器實例。"""
    global websocket_manager
    websocket_manager = manager

class WebSocketLogHandler(logging.Handler):
    """一個自訂的日誌處理程序，可將日誌轉發到 WebSocket 連線。"""
    def emit(self, record):
        if websocket_manager:
            log_entry = {
                "event_type": "LOG_MESSAGE",
                "payload": {
                    "timestamp": record.created,
                    "level": record.levelname,
                    "message": self.format(record)
                }
            }
            # 使用 asyncio.create_task 在背景廣播，避免阻塞
            asyncio.create_task(websocket_manager.broadcast(log_entry))

def setup_logging(log_filename: str = None):
    """
    設定全域日誌記錄。
    :param log_filename: 如果提供，將使用此檔名，否則使用預設值。
    """
    log_formatter = logging.Formatter(
        "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
    )

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 1. 控制台處理程序
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    root_logger.addHandler(console_handler)

    # 2. 檔案處理程序 (可配置路徑和檔名)
    archive_dir = settings.ARCHIVE_FOLDER_NAME
    if not os.path.exists(archive_dir):
        os.makedirs(archive_dir)

    if log_filename is None:
        tz = pytz.timezone('Asia/Taipei')
        timestamp = datetime.now(tz).strftime('%Y-%m-%dT%H-%M-%S')
        log_filename = f"後端系統日誌_{timestamp}.txt"

    log_file_path = os.path.join(archive_dir, log_filename)

    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=5*1024*1024, backupCount=2, encoding='utf-8'
    )
    file_handler.setFormatter(log_formatter)
    root_logger.addHandler(file_handler)

    # 3. WebSocket 處理程序
    websocket_handler = WebSocketLogHandler()
    websocket_handler.setLevel(logging.INFO)
    websocket_handler.setFormatter(logging.Formatter("%(message)s"))
    root_logger.addHandler(websocket_handler)

    logging.info(f"日誌系統初始化完畢。日誌檔案將儲存於 '{os.path.abspath(log_file_path)}'")
    return log_file_path
