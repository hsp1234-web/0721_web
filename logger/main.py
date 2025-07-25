import asyncio
import json
import logging
import os
import time
from multiprocessing import Queue
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Tuple

import duckdb
import pandas as pd

# 循環導入，但對於這種架構是必要的
# 在主應用程式中，main 會先被加載
from main import manager

# --- 常數設定 ---
DB_PATH = os.path.join(
    os.path.dirname(__file__), "..", "database", "system_logs.duckdb"
)
LOG_TABLE_NAME = "logs"
MONITOR_TABLE_NAME = "monitoring"
BATCH_SIZE = 50
BATCH_TIMEOUT = 5

# --- 資料庫結構 ---
LOG_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {LOG_TABLE_NAME} (
    timestamp TIMESTAMP,
    level VARCHAR,
    process_name VARCHAR,
    message VARCHAR
);
"""

MONITOR_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS {MONITOR_TABLE_NAME} (
    timestamp TIMESTAMP,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT
);
"""


def initialize_database() -> None:
    """初始化 DuckDB 資料庫和資料表。"""
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)
    with duckdb.connect(DB_PATH) as con:
        con.execute(LOG_SCHEMA)
        con.execute(MONITOR_SCHEMA)


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
            # 因為這是從不同的執行緒呼叫，我們需要一個事件迴圈
            # FastAPI 的 `manager.broadcast` 是非同步的
            asyncio.run(manager.broadcast(json.dumps(protocol_message)))
        except Exception as e:
            # 在日誌處理程序中打印錯誤可能很棘手，避免無限循環
            print(f"在 WebSocketLogHandler 中發生錯誤: {e}")


def setup_logging() -> None:
    """設定全域日誌記錄，將日誌同時輸出到控制台和 WebSocket。"""
    # 建立 WebSocket 處理程序
    websocket_handler = WebSocketLogHandler()
    websocket_handler.setLevel(logging.INFO)

    # 設定日誌格式
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    websocket_handler.setFormatter(formatter)

    # 獲取根 logger 並添加我們的處理程序
    # 這將捕獲來自 FastAPI、Uvicorn 和我們自己應用程式的日誌
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.addHandler(websocket_handler)

    # (可選) 如果你還想在伺服器控制台中看到日誌
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    root_logger.addHandler(stream_handler)

    logging.info("日誌系統已初始化，WebSocket 處理程序已掛載。")


# 移除舊的基於進程的日誌記錄器和測試代碼
# initialize_database 和相關的 DuckDB 邏輯如果不再需要，也可以考慮移除
# 但為了保留數據持久化能力，我們暫時保留它，儘管它目前未被 setup_logging 使用
