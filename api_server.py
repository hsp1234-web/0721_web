# -*- coding: utf-8 -*-
import os
import sqlite3
from pathlib import Path
from flask import Flask, jsonify
from flask_cors import CORS

# --- 資料庫設定 ---
# 透過環境變數取得資料庫檔案路徑，如果未設定，則使用預設值
DB_FILE = Path(os.getenv("DB_FILE", "/tmp/state.db"))

app = Flask(__name__)
CORS(app)

def get_db_connection():
    """建立唯讀的資料庫連線"""
    try:
        # 使用 URI 模式確保可以設定唯讀模式
        conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.OperationalError as e:
        print(f"無法連線到資料庫 {DB_FILE}: {e}")
        # 在這裡可以引發一個自訂的例外，或者回傳 None
        # 這將幫助 API 端點優雅地處理資料庫無法存取的問題
        raise

@app.route('/api/status', methods=['GET'])
def get_status():
    """提供主狀態表的數據"""
    try:
        conn = get_db_connection()
        status = conn.execute('SELECT * FROM status_table WHERE id = 1').fetchone()
        conn.close()
        if status is None:
            # 即使資料庫存在但沒有資料，也回傳錯誤
            return jsonify({"error": "No status data found"}), 404
        # 將 sqlite3.Row 物件轉換為字典
        return jsonify(dict(status))
    except Exception as e:
        # 捕捉所有可能的例外，包括 get_db_connection 引發的錯誤
        return jsonify({"error": f"Could not retrieve status: {e}"}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """提供一個簡單的健康檢查端點，確認服務是否在運行"""
    return jsonify({"status": "ok"})

@app.route('/api/logs', methods=['GET'])
def get_logs():
    """提供最新的 50 條日誌，以支援更詳細的前端顯示"""
    try:
        conn = get_db_connection()
        # 增加日誌的拉取數量
        logs = conn.execute('SELECT * FROM log_table ORDER BY id DESC LIMIT 50').fetchall()
        conn.close()
        # 將 sqlite3.Row 物件列表轉換為字典列表
        return jsonify([dict(log) for log in logs])
    except Exception as e:
        return jsonify({"error": f"Could not retrieve logs: {e}"}), 500

def run_api_server():
    """啟動 Flask API 伺服器"""
    # 從環境變數讀取埠號，如果未設定，則使用預設值 8080
    port = int(os.getenv("API_PORT", 8080))
    # 使用 '0.0.0.0' 讓伺服器可以從外部存取
    app.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    if not DB_FILE.exists():
        print(f"錯誤：資料庫檔案 {DB_FILE} 不存在。請先啟動主應用程式 (run.py) 來初始化資料庫。")
    else:
        print(f"✅ API 伺服器啟動，監聽埠口 {os.getenv('API_PORT', 8080)}")
        print(f"📖 讀取資料庫位置: {DB_FILE}")
        run_api_server()
