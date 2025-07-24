# -*- coding: utf-8 -*-
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("logs.sqlite")

def main():
    """
    一個簡單的腳本，用於驗證 logs.sqlite 資料庫的內容。
    """
    if not DB_PATH.exists():
        print(f"🔴 [錯誤] 資料庫檔案 '{DB_PATH}' 不存在。")
        sys.exit(1)

    try:
        with sqlite3.connect(DB_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM logs")
            count = cursor.fetchone()[0]

            if count > 0:
                print(f"✅ [成功] 在 '{DB_PATH}' 中找到 {count} 條日誌。")
                print("--- 日誌預覽 (前 5 條) ---")
                cursor.execute("SELECT level, message FROM logs ORDER BY id LIMIT 5")
                for row in cursor.fetchall():
                    print(f"[{row[0]}] {row[1]}")
                print("-------------------------")
                sys.exit(0)
            else:
                print(f"🟠 [警告] 資料庫 '{DB_PATH}' 是空的。")
                sys.exit(1)

    except sqlite3.Error as e:
        print(f"🔴 [錯誤] 讀取 SQLite 資料庫時發生錯誤: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
