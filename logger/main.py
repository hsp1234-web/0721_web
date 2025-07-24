import duckdb
import time
import os
import pandas as pd
from multiprocessing import Queue
from threading import Thread, Event

# --- 常數設定 ---
DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'system_logs.duckdb')
LOG_TABLE_NAME = 'logs'
MONITOR_TABLE_NAME = 'monitoring'
BATCH_SIZE = 50  # 每收集 50 條日誌就寫入一次
BATCH_TIMEOUT = 5  # 或每 5 秒寫入一次，以先到者為準

# --- 資料庫結構 ---
LOG_SCHEMA = """
CREATE TABLE IF NOT EXISTS {} (
    timestamp TIMESTAMP,
    level VARCHAR,
    process_name VARCHAR,
    message VARCHAR
);
""".format(LOG_TABLE_NAME)

MONITOR_SCHEMA = """
CREATE TABLE IF NOT EXISTS {} (
    timestamp TIMESTAMP,
    cpu_usage FLOAT,
    memory_usage FLOAT,
    disk_usage FLOAT
);
""".format(MONITOR_TABLE_NAME)


def initialize_database():
    """初始化 DuckDB 資料庫和資料表"""
    # 確保資料庫目錄存在
    db_dir = os.path.dirname(DB_PATH)
    os.makedirs(db_dir, exist_ok=True)

    con = duckdb.connect(DB_PATH)
    con.execute(LOG_SCHEMA)
    con.execute(MONITOR_SCHEMA)
    con.close()


def logger_process(log_queue: Queue, stop_event: Event):
    """
    日誌消費者進程。
    從佇列中讀取日誌和監控數據，並批次寫入 DuckDB。
    """
    print("[日誌進程] 啟動。")
    initialize_database()
    con = duckdb.connect(DB_PATH)

    log_batch = []
    monitor_batch = []
    last_write_time = time.time()

    def write_to_db():
        nonlocal last_write_time
        if not log_batch and not monitor_batch:
            return

        try:
            if log_batch:
                # 轉換為 Pandas DataFrame
                df_log = pd.DataFrame(log_batch, columns=['timestamp', 'level', 'process_name', 'message'])
                # 使用 DataFrame 插入
                con.register('log_batch_df', df_log)
                con.execute(f"INSERT INTO {LOG_TABLE_NAME} SELECT * FROM log_batch_df")
                con.unregister('log_batch_df')
                log_batch.clear()

            if monitor_batch:
                # 轉換為 Pandas DataFrame
                df_monitor = pd.DataFrame(monitor_batch, columns=['timestamp', 'cpu_usage', 'memory_usage', 'disk_usage'])
                 # 使用 DataFrame 插入
                con.register('monitor_batch_df', df_monitor)
                con.execute(f"INSERT INTO {MONITOR_TABLE_NAME} SELECT * FROM monitor_batch_df")
                con.unregister('monitor_batch_df')
                monitor_batch.clear()

            # 這邊的 print 必須在 clear() 之前才能正確顯示數量
            # print(f"[日誌進程] 已將 {len(log_batch)} 條日誌和 {len(monitor_batch)} 條監控數據寫入 DuckDB。")

        except Exception as e:
            print(f"[日誌進程] 寫入資料庫時發生錯誤: {e}")

        last_write_time = time.time()

    while not stop_event.is_set():
        try:
            # 非阻塞地從佇列中獲取數據
            item = log_queue.get(timeout=1)

            if item is None: # 收到停止信號
                break

            item_type = item.get("type", "log")
            data = item.get("data")

            if item_type == "log":
                log_batch.append(data)
            elif item_type == "monitor":
                monitor_batch.append(data)

            # 檢查是否滿足批次寫入條件
            if len(log_batch) >= BATCH_SIZE or len(monitor_batch) >= BATCH_SIZE:
                write_to_db()

        except Exception: # get from queue timed out
            # 佇列為空，檢查是否滿足超時寫入條件
            if time.time() - last_write_time > BATCH_TIMEOUT:
                write_to_db()

    print("[日誌進程] 收到停止信號，正在寫入剩餘日誌...")
    write_to_db()  # 寫入所有剩餘的日誌
    con.close()
    print("[日誌進程] 已關閉。")

if __name__ == '__main__':
    # 此部分用於直接測試 logger/main.py
    print("正在以獨立模式測試日誌系統...")
    test_log_queue = Queue()
    test_stop_event = Event()

    # 啟動日誌進程
    logger_thread = Thread(target=logger_process, args=(test_log_queue, test_stop_event))
    logger_thread.start()

    # 模擬應用程式發送日誌
    test_log_queue.put({"type": "log", "data": (time.strftime('%Y-%m-%d %H:%M:%S'), "INFO", "MainApp", "應用程式啟動")})
    test_log_queue.put({"type": "monitor", "data": (time.strftime('%Y-%m-%d %H:%M:%S'), 10.5, 25.2, 50.1)})

    time.sleep(2)

    for i in range(60):
        test_log_queue.put({"type": "log", "data": (time.strftime('%Y-%m-%d %H:%M:%S'), "DEBUG", "Worker", f"處理任務 #{i}")})
        time.sleep(0.05)

    # 等待批次超時寫入
    print("等待 6 秒讓超時寫入觸發...")
    time.sleep(6)

    # 停止日誌進程
    print("正在停止日誌進程...")
    test_stop_event.set()
    logger_thread.join()
    print("測試完成。請檢查 'database/system_logs.duckdb' 檔案。")
