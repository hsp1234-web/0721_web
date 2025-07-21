# archiver.py

import sqlite3
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ARCHIVE_DIR = Path("/content/作戰日誌歸檔")

def generate_final_log_file(db_path: Path):
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)

    with conn:
        cursor = conn.execute("SELECT timestamp, level, message FROM logs ORDER BY id ASC")
        logs = cursor.fetchall()

    timestamp = datetime.datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"作戰日誌_{timestamp}.txt"
    log_filepath = ARCHIVE_DIR / log_filename

    with open(log_filepath, "w", encoding="utf-8") as f:
        for timestamp, level, message in logs:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    print(f"最終日誌報告已生成並歸檔至: {log_filepath}")
