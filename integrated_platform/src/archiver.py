# archiver.py

import sqlite3
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ARCHIVE_DIR = Path("log_archive")

def generate_final_log_file(db_path: Path):
    """
    職責：在任務結束時，從 SQLite 生成一份完整的 .txt 日誌報告，
          並將其儲存到一個固定的、獨立的中文資料夾中。
    """
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    try:
        conn = sqlite3.connect(db_path)
        with conn:
            cursor = conn.execute("SELECT timestamp, level, message FROM logs ORDER BY id ASC")
            logs = cursor.fetchall()
    except sqlite3.Error as e:
        print(f"讀取資料庫時發生錯誤: {e}")
        return

    timestamp = datetime.datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"log_report_{timestamp}.txt"
    final_filepath = ARCHIVE_DIR / log_filename

    try:
        with open(final_filepath, "w", encoding="utf-8") as f:
            for ts, level, message in logs:
                f.write(f"[{ts}] [{level}] {message}\n")
        print(f"最終日誌報告已生成並歸檔至: {final_filepath}")
    except IOError as e:
        print(f"寫入日誌檔案時發生錯誤: {e}")
