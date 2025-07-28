# -*- coding: utf-8 -*-
"""
資料庫模組

負責初始化 SQLite 資料庫和建立資料表。
"""

import sqlite3

def initialize_database(db_conn_or_path):
    """
    在給定的 SQLite 資料庫連接或路徑上建立所需的資料表。

    :param db_conn_or_path: 一個 sqlite3 連接物件或資料庫檔案的路徑。
    """
    is_path = isinstance(db_conn_or_path, str)
    con = sqlite3.connect(db_conn_or_path) if is_path else db_conn_or_path

    try:
        cur = con.cursor()

        # 建立 execution_log 表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS execution_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                worker_id INTEGER,
                task_name TEXT,
                log_level TEXT,
                message TEXT
            )
        ''')

        # 建立 performance_metrics 表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                worker_id INTEGER,
                task_name TEXT,
                duration_seconds REAL,
                cpu_usage_percent REAL,
                memory_usage_mb REAL
            )
        ''')

        # 建立 error_reports 表
        cur.execute('''
            CREATE TABLE IF NOT EXISTS error_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                worker_id INTEGER,
                task_name TEXT,
                error_message TEXT,
                traceback_details TEXT
            )
        ''')

        con.commit()
        if is_path:
            con.close()
        # 如果傳入的是連接物件，我們不在此處關閉它
        print(f"資料庫初始化成功。")
    except sqlite3.Error as e:
        print(f"資料庫初始化時發生錯誤：{e}")
        if is_path:
            con.close()
        raise

def get_db_connection(db_path):
    """
    取得一個資料庫連接。

    :param db_path: 資料庫檔案的路徑。
    :return: 一個 sqlite3 連接物件。
    """
    try:
        con = sqlite3.connect(db_path)
        return con
    except sqlite3.Error as e:
        print(f"無法連接到資料庫 '{db_path}': {e}")
        return None
