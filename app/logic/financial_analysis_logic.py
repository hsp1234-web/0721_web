# -*- coding: utf-8 -*-
"""
金融數據分析相關的業務邏輯
"""
import uuid
import subprocess
import sqlite3
from flask import jsonify
from app.db import DATABASE_FILE

# 指向普羅米修斯之火專案的 run.py
PROMETHEUS_RUN_SCRIPT = "ALL_DATE/0709_wolf_88/run.py"
PROMETHEUS_PROJECT_DIR = "ALL_DATE/0709_wolf_88"

def start_feature_store_build():
    """
    非同步觸發一個 'build-feature-store' 的背景任務。
    """
    task_id = str(uuid.uuid4())
    log_file_path = f"/tmp/prometheus_build_{task_id}.log"

    try:
        # 1. 在資料庫中記錄這個新任務
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        # 我們可以擴充現有的表或建立一個新表，這裡為了簡單先用 print
        print(f"在資料庫中為金融分析任務 {task_id} 建立紀錄。")
        # 實際應寫入資料庫
        # cursor.execute(
        #     "INSERT INTO analysis_tasks (id, task_type, status, log_file) VALUES (?, ?, ?, ?)",
        #     (task_id, "build_feature_store", "starting", log_file_path)
        # )
        # conn.commit()
        conn.close()

        # 2. 使用 subprocess 在背景啟動長時間執行的任務
        # 我們將 stdout 和 stderr 都重新導向到一個日誌檔案中
        command = [
            "poetry", "run", "python", PROMETHEUS_RUN_SCRIPT, "build-feature-store"
        ]

        with open(log_file_path, "w") as log_file:
            # Popen 不會阻塞，它會立即返回
            subprocess.Popen(
                command,
                cwd=PROMETHEUS_PROJECT_DIR, # 在該專案目錄下執行
                stdout=log_file,
                stderr=subprocess.STDOUT
            )

        message = f"已成功啟動 'build-feature-store' 任務。任務 ID: {task_id}。日誌請查看: {log_file_path}"
        return jsonify({"status": "success", "message": message, "task_id": task_id}), 202

    except FileNotFoundError:
        # 如果 poetry 不在 PATH 中，會發生這個錯誤
        error_msg = "錯誤：'poetry' 指令未找到。請確保 Poetry 已經安裝並且在系統的 PATH 中。"
        return jsonify({"status": "error", "message": error_msg}), 500
    except Exception as e:
        error_msg = f"啟動分析任務時發生未預期的錯誤: {e}"
        print(error_msg)
        return jsonify({"status": "error", "message": "伺服器內部錯誤"}), 500

# 之後可以加入查詢數據的函式
# def get_factor_data(factor_name):
#     ...
