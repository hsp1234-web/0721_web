from pathlib import Path
from integrated_platform.src.log_manager import LogManager

db_path = Path("test_logs.sqlite")
if db_path.exists():
    db_path.unlink()

log_manager = LogManager(db_path)
log_manager.log("INFO", "這是一個測試日誌。")
log_manager.log("WARNING", "這是一個警告訊息。")
log_manager.close()

print(f"測試資料庫 '{db_path}' 已建立。")
