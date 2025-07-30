# -*- coding: utf-8 -*-
import os
import sqlite3
import json
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允許所有來源的跨域請求

DB_FILE = Path(os.getenv("DB_FILE", "/tmp/state.db"))

def get_db_connection():
    """建立到唯讀資料庫的連線"""
    conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/status', methods=['GET'])
def get_status():
    """提供主狀態表的數據"""
    try:
        conn = get_db_connection()
        status = conn.execute('SELECT * FROM status_table WHERE id = 1').fetchone()
        conn.close()
        if status is None:
            return jsonify({"error": "No status data found"}), 404
        # 將 status (一個 sqlite3.Row 物件) 轉換為字典
        return jsonify(dict(status))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """提供一個簡單的健康檢查端點"""
    # 在未來，這裡可以擴展為檢查資料庫連接等
    return jsonify({"status": "ok"})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """提供最新的 10 條日誌"""
    try:
        conn = get_db_connection()
        logs = conn.execute('SELECT * FROM log_table ORDER BY id DESC LIMIT 10').fetchall()
        conn.close()
        # 將日誌列表 (sqlite3.Row 物件的列表) 轉換為字典的列表
        return jsonify([dict(log) for log in logs])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # 從環境變數讀取埠號，預設為 8080 以匹配 Colab 啟動器
    port = int(os.environ.get("API_PORT", 8080))
    app.run(host='0.0.0.0', port=port)
