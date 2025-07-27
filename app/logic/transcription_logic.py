# -*- coding: utf-8 -*-
"""
錄音轉寫相關的業務邏輯
"""
import uuid
import sqlite3
import time
from pathlib import Path
from flask import request, jsonify

from app.db import DATABASE_FILE

# --- 常數設定 ---
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

def upload_and_transcribe():
    """
    處理檔案上傳並模擬轉寫過程。
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "缺少上傳的檔案"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"status": "error", "message": "未選擇檔案"}), 400

    task_id = str(uuid.uuid4())
    filepath = UPLOAD_DIR / f"{task_id}_{file.filename}"

    try:
        # 1. 儲存檔案
        file.save(filepath)

        # 2. 在資料庫中建立任務
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO transcription_tasks (id, original_filepath, status, result)
            VALUES (?, ?, ?, ?)
            """,
            (task_id, str(filepath), "processing", "")
        )
        conn.commit()
        conn.close()

        # 3. 模擬同步轉寫過程 (未來可以換成非同步 worker)
        time.sleep(5)  # 模擬耗時的轉寫工作
        transcribed_text = f"這是 '{file.filename}' 的模擬轉寫結果。"

        # 4. 更新資料庫中的任務狀態
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE transcription_tasks SET status = ?, result = ? WHERE id = ?",
            ("completed", transcribed_text, task_id)
        )
        conn.commit()
        conn.close()

        return jsonify({"task_id": task_id}), 202

    except Exception as e:
        # 這裡應該使用 logger 記錄錯誤
        print(f"處理上傳時發生錯誤: {e}")
        return jsonify({"status": "error", "message": "伺服器內部錯誤"}), 500

def get_task_status(task_id):
    """
    根據 task_id 查詢任務狀態。
    """
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        # 讓查詢結果可以像字典一樣用欄位名存取
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM transcription_tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        conn.close()

        if task is None:
            return jsonify({"status": "error", "message": "找不到任務"}), 404

        # 將 Row 物件轉換為字典
        return jsonify(dict(task))

    except Exception as e:
        print(f"查詢狀態時發生錯誤: {e}")
        return jsonify({"status": "error", "message": "伺服器內部錯誤"}), 500
