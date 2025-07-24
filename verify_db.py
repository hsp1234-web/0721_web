import duckdb
import pandas as pd

DB_PATH = "database/system_logs.duckdb"

try:
    con = duckdb.connect(DB_PATH, read_only=True)

    print("--- 查詢 'logs' 資料表 ---")
    logs_df = con.table('logs').to_df()
    if not logs_df.empty:
        print(logs_df)
    else:
        print("'logs' 資料表為空。")

    print("\n--- 查詢 'monitoring' 資料表 ---")
    monitoring_df = con.table('monitoring').to_df()
    if not monitoring_df.empty:
        print(monitoring_df)
    else:
        print("'monitoring' 資料表為空。")

    con.close()

except Exception as e:
    print(f"查詢資料庫時發生錯誤: {e}")
