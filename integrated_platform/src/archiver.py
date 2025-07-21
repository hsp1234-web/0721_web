# archiver.py

import sqlite3
import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

def generate_final_log_file(db_path: Path, output_dir: Path):
    output_dir.mkdir(exist_ok=True)
    conn = sqlite3.connect(db_path)

    with conn:
        cursor = conn.execute("SELECT timestamp, level, message FROM logs ORDER BY id ASC")
        logs = cursor.fetchall()

    timestamp = datetime.datetime.now(ZoneInfo("Asia/Taipei")).strftime("%Y-%m-%d_%H-%M-%S")
    log_filename = f"作戰日誌_{timestamp}.txt"
    log_filepath = output_dir / log_filename

    with open(log_filepath, "w", encoding="utf-8") as f:
        for timestamp, level, message in logs:
            f.write(f"[{timestamp}] [{level}] {message}\n")

    print(f"最終日誌報告已生成: {log_filepath}")
