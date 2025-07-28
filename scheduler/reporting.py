# -*- coding: utf-8 -*-
"""
報告生成模組

提供函式以從資料庫生成執行摘要和效能報告。
"""

import sqlite3

def _get_db_connection(db_path):
    """安全地獲取資料庫連接。"""
    try:
        # 使用唯讀模式 URI，防止意外寫入
        # file:{}?mode=ro
        db_uri = f"file:{db_path}?mode=ro"
        con = sqlite3.connect(db_uri, uri=True)
        return con
    except sqlite3.OperationalError:
        print(f"報告錯誤：找不到或無法以唯讀模式開啟資料庫檔案 '{db_path}'。")
        return None

def generate_summary_report(db_path):
    """
    生成執行摘要報告並印出到控制台。
    """
    print("\n" + "="*30)
    print("      執行摘要報告")
    print("="*30)

    con = _get_db_connection(db_path)
    if not con:
        return

    try:
        cur = con.cursor()

        # 獲取成功和失敗的任務總數
        cur.execute("SELECT COUNT(*) FROM performance_metrics")
        success_count = cur.fetchone()[0]

        cur.execute("SELECT COUNT(*) FROM error_reports")
        fail_count = cur.fetchone()[0]

        total_tasks = success_count + fail_count
        print(f"總任務數: {total_tasks}")
        print(f"  - 成功: {success_count}")
        print(f"  - 失敗: {fail_count}")

        if fail_count > 0:
            print("\n--- 失敗任務詳情 ---")
            cur.execute("SELECT timestamp, worker_id, task_name, error_message FROM error_reports ORDER BY timestamp")
            failed_tasks = cur.fetchall()
            for task in failed_tasks:
                print(f"  - 時間: {task[0]}")
                print(f"    工作者ID: {task[1]}, 任務名稱: {task[2]}")
                print(f"    錯誤: {task[3]}")

        con.close()
    except Exception as e:
        print(f"生成摘要報告時發生錯誤: {e}")
    finally:
        if con:
            con.close()
    print("="*30 + "\n")


def generate_performance_report(db_path):
    """
    生成效能瓶頸報告並印出到控制台。
    """
    print("\n" + "="*30)
    print("      效能瓶頸報告")
    print("="*30)

    con = _get_db_connection(db_path)
    if not con:
        return

    try:
        cur = con.cursor()

        # 查詢最耗時的任務
        print("\n--- Top 3 最耗時任務 ---")
        cur.execute("SELECT task_name, duration_seconds FROM performance_metrics ORDER BY duration_seconds DESC LIMIT 3")
        slowest_tasks = cur.fetchall()
        if not slowest_tasks:
            print("  (無效能數據)")
        else:
            for i, task in enumerate(slowest_tasks):
                print(f"  {i+1}. {task[0]}: {task[1]:.4f} 秒")

        # 查詢 CPU 使用率最高的任務
        print("\n--- Top 3 CPU 使用率最高任務 ---")
        cur.execute("SELECT task_name, cpu_usage_percent FROM performance_metrics ORDER BY cpu_usage_percent DESC LIMIT 3")
        cpu_tasks = cur.fetchall()
        if not cpu_tasks:
            print("  (無效能數據)")
        else:
            for i, task in enumerate(cpu_tasks):
                print(f"  {i+1}. {task[0]}: {task[1]:.2f}%")

        # 查詢記憶體佔用最高的任務
        print("\n--- Top 3 記憶體佔用最高任務 ---")
        cur.execute("SELECT task_name, memory_usage_mb FROM performance_metrics ORDER BY memory_usage_mb DESC LIMIT 3")
        mem_tasks = cur.fetchall()
        if not mem_tasks:
            print("  (無效能數據)")
        else:
            for i, task in enumerate(mem_tasks):
                print(f"  {i+1}. {task[0]}: {task[1]:.2f} MB")

        con.close()
    except Exception as e:
        print(f"生成效能報告時發生錯誤: {e}")
    finally:
        if con:
            con.close()
    print("="*30 + "\n")
