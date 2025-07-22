# -*- coding: utf-8 -*-
"""
轉寫服務核心模組。

此檔案提供轉寫服務所需的資料庫初始化功能。
"""
import logging
import multiprocessing as mp
import aiosqlite
import sys
from pathlib import Path

from prometheus.core.config import config

# --- 設定 ---
# 從全域設定檔讀取轉寫服務的專屬設定
transcriber_config = config.get('transcriber', {})
DATABASE_FILE = Path(transcriber_config.get('database_file', 'data/transcriber.db'))
UPLOAD_DIR = Path(transcriber_config.get('upload_dir', 'data/uploads'))

# 取得一個日誌記錄器
logger = logging.getLogger(__name__)

async def initialize_database() -> None:
    """
    初始化資料庫與上傳目錄。

    如果資料庫或指定的資料表不存在，此函式會自動建立它們。
    """
    try:
        # 確保上傳目錄存在
        UPLOAD_DIR.mkdir(exist_ok=True)

        async with aiosqlite.connect(DATABASE_FILE) as db:
            # 建立轉寫任務資料表
            await db.execute(
                """
            CREATE TABLE IF NOT EXISTS transcription_tasks (
                id TEXT PRIMARY KEY,
                original_filepath TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
                result_text TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            # 建立一個觸發器，在更新資料列時自動更新 updated_at 欄位
            await db.execute(
                """
            CREATE TRIGGER IF NOT EXISTS update_transcription_tasks_updated_at
            AFTER UPDATE ON transcription_tasks
            FOR EACH ROW
            BEGIN
                UPDATE transcription_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """
            )

            await db.commit()
        logger.info("資料庫 '%s' 和目錄 '%s' 已成功初始化。", DATABASE_FILE, UPLOAD_DIR)
    except aiosqlite.Error as e:
        logger.exception("資料庫初始化失敗: %s", e)
        raise

# 日誌系統已被移除，將統一使用 prometheus 的中央日誌系統。


from prometheus.core.config import config

# --- 設定 ---
transcriber_config = config.get('transcriber', {})
DATABASE_FILE = Path(transcriber_config.get('database_file', 'data/transcriber.db'))
UPLOAD_DIR = Path(transcriber_config.get('upload_dir', 'data/uploads'))
logger = logging.getLogger(__name__)


async def initialize_database() -> None:
    """初始化資料庫和上傳目錄, 如果資料表不存在, 則建立它."""
    try:
        # 建立上傳目錄
        UPLOAD_DIR.mkdir(exist_ok=True)

        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                """
            CREATE TABLE IF NOT EXISTS transcription_tasks (
                id TEXT PRIMARY KEY,
                original_filepath TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed'
                result_text TEXT,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
            )

            await db.execute(
                """
            CREATE TRIGGER IF NOT EXISTS update_transcription_tasks_updated_at
            AFTER UPDATE ON transcription_tasks
            FOR EACH ROW
            BEGIN
                UPDATE transcription_tasks SET updated_at = CURRENT_TIMESTAMP WHERE id = OLD.id;
            END;
            """
            )

            await db.commit()
        logger.info("資料庫 '%s' 和目錄 '%s' 已成功初始化.", DATABASE_FILE, UPLOAD_DIR)
    except aiosqlite.Error as e:
        logger.exception("資料庫初始化失敗: %s", e)
        raise


# 日誌系統已被移除，將統一使用 prometheus 的中央日誌系統。
