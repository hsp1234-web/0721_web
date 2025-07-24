import os
import time
from multiprocessing import Queue
from threading import Event, Thread
from typing import Any, Dict, List, Optional, Tuple

import duckdb
import pandas as pd

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


def logger_process(
    log_queue: "Queue[Optional[Dict[str, Any]]]", stop_event: Event
) -> None:
    """日誌消費者進程。

    從佇列中讀取日誌和監控數據，並批次寫入 DuckDB。
    """
    print("[日誌進程] 啟動。")
    initialize_database()
    con = duckdb.connect(DB_PATH)

    log_batch: List[Tuple[Any, ...]] = []
    monitor_batch: List[Tuple[Any, ...]] = []
    last_write_time = time.time()

    def write_to_db() -> None:
        nonlocal last_write_time
        if not log_batch and not monitor_batch:
            return

        try:
            if log_batch:
                df_log = pd.DataFrame(
                    log_batch, columns=["timestamp", "level", "process_name", "message"]
                )
                con.register("log_batch_df", df_log)
                con.execute(
                    f"INSERT INTO {LOG_TABLE_NAME} SELECT * FROM log_batch_df"  # nosec B608
                )
                con.unregister("log_batch_df")
                log_batch.clear()

            if monitor_batch:
                df_monitor = pd.DataFrame(
                    monitor_batch,
                    columns=["timestamp", "cpu_usage", "memory_usage", "disk_usage"],
                )
                con.register("monitor_batch_df", df_monitor)
                con.execute(
                    f"INSERT INTO {MONITOR_TABLE_NAME} SELECT * FROM monitor_batch_df"  # nosec B608
                )
                con.unregister("monitor_batch_df")
                monitor_batch.clear()
        except Exception as e:
            print(f"[日誌進程] 寫入資料庫時發生錯誤: {e}")
        finally:
            last_write_time = time.time()

    while not stop_event.is_set():
        try:
            item = log_queue.get(timeout=1)
            if item is None:
                break
            data = item.get("data")
            if data:
                if item.get("type", "log") == "log":
                    log_batch.append(data)
                else:
                    monitor_batch.append(data)

            if len(log_batch) >= BATCH_SIZE or len(monitor_batch) >= BATCH_SIZE:
                write_to_db()
        except Exception:  # Queue.empty or other errors
            if time.time() - last_write_time > BATCH_TIMEOUT:
                write_to_db()

    print("[日誌進程] 收到停止信號，正在寫入剩餘日誌...")
    write_to_db()
    con.close()
    print("[日誌進程] 已關閉。")


if __name__ == "__main__":
    print("正在以獨立模式測試日誌系統...")
    test_log_queue: "Queue[Optional[Dict[str, Any]]]" = Queue()
    test_stop_event = Event()

    logger_thread = Thread(
        target=logger_process, args=(test_log_queue, test_stop_event)
    )
    logger_thread.start()

    test_log_queue.put(
        {
            "type": "log",
            "data": (
                time.strftime("%Y-%m-%d %H:%M:%S"),
                "INFO",
                "MainApp",
                "應用程式啟動",
            ),
        }
    )
    test_log_queue.put(
        {
            "type": "monitor",
            "data": (time.strftime("%Y-%m-%d %H:%M:%S"), 10.5, 25.2, 50.1),
        }
    )
    time.sleep(2)

    for i in range(60):
        test_log_queue.put(
            {
                "type": "log",
                "data": (
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    "DEBUG",
                    "Worker",
                    f"處理任務 #{i}",
                ),
            }
        )
        time.sleep(0.05)

    print("等待 6 秒讓超時寫入觸發...")
    time.sleep(6)

    print("正在停止日誌進程...")
    test_stop_event.set()
    logger_thread.join()
    print("測試完成。請檢查 'database/system_logs.duckdb' 檔案。")
