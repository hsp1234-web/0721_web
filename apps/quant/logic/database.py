# -*- coding: utf-8 -*-
"""
數據庫邏輯 (Database)

負責所有與數據庫的互動，包括數據的持久化儲存和讀取。
為了保持微服務的獨立性，我們在這裡使用一個簡單的 SQLite 資料庫。
"""
import sqlite3
from pathlib import Path

import pandas as pd

# --- 資料庫設定 ---
DB_FILE = Path("quant_app.db")

class DBManager:
    """
    一個簡單的 SQLite 資料庫管理器。
    """
    def __init__(self, db_file: str = DB_FILE):
        """
        初始化資料庫管理器並建立連接。
        """
        self.db_file = db_file
        self.conn = None
        try:
            self.conn = sqlite3.connect(self.db_file, check_same_thread=False)
            # 使用 `check_same_thread=False` 允許在 FastAPI 的不同執行緒中使用
            print(f"成功連接到資料庫: {self.db_file}")
        except sqlite3.Error as e:
            print(f"資料庫連接錯誤: {e}")
            raise

    def initialize_tables(self):
        """
        如果表不存在，則創建它們。
        """
        if not self.conn:
            return

        try:
            cursor = self.conn.cursor()
            # 創建一個用於儲存回測結果的表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    stock_id TEXT NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    initial_capital REAL,
                    final_value REAL,
                    total_return_pct REAL,
                    trade_count INTEGER
                )
            """)
            self.conn.commit()
            print("資料表 'backtest_results' 已成功初始化。")
        except sqlite3.Error as e:
            print(f"建立資料表時發生錯誤: {e}")

    def save_backtest_result(self, result: dict):
        """
        將回測結果儲存到資料庫。

        :param result: 從 analysis.run_simple_backtest() 返回的結果字典。
        """
        if not self.conn or "error" in result:
            return

        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO backtest_results (
                    stock_id, start_date, end_date, initial_capital,
                    final_value, total_return_pct, trade_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                result.get("stock_id"),
                result.get("start_date"),
                result.get("end_date"),
                result.get("initial_capital"),
                result.get("final_value"),
                result.get("total_return_pct"),
                result.get("trade_count"),
            ))
            self.conn.commit()
            print(f"已成功將股票 {result.get('stock_id')} 的回測結果存入資料庫。")
        except sqlite3.Error as e:
            print(f"儲存回測結果時發生錯誤: {e}")

    def get_all_backtest_results(self) -> pd.DataFrame:
        """
        從資料庫讀取所有回測結果。
        """
        if not self.conn:
            return pd.DataFrame() # 返回空的 DataFrame

        try:
            df = pd.read_sql_query("SELECT * FROM backtest_results ORDER BY run_timestamp DESC", self.conn)
            return df
        except Exception as e:
            print(f"讀取回測結果時發生錯誤: {e}")
            return pd.DataFrame()

    def close(self):
        """
        關閉資料庫連接。
        """
        if self.conn:
            self.conn.close()
            print("資料庫連接已關閉。")

# --- 全局實例 ---
# 可以在 App 啟動時創建一個全局的 DBManager 實例
db_manager = DBManager()

# 在 App 啟動時初始化資料表
db_manager.initialize_tables()
