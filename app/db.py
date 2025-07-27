# -*- coding: utf-8 -*-
"""
資料庫管理模組
"""
import sqlite3
from pathlib import Path

DATABASE_FILE = Path("app_data.db")

def initialize_database():
    """
    建立資料庫和所需的資料表（如果它們還不存在）。
    """
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    # 建立 transcription_tasks 資料表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transcription_tasks (
            id TEXT PRIMARY KEY,
            original_filepath TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    print(f"資料庫 '{DATABASE_FILE}' 已成功初始化。")
