# -*- coding: utf-8 -*-
import pytest
import sqlite3
import json
from pathlib import Path
import os
import sys

# 將專案根目錄添加到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 在導入 app 之前設定環境變數
os.environ["DB_FILE"] = str(PROJECT_ROOT / "tests" / "test.db")
from api_server import app

@pytest.fixture
def client():
    """設定一個 Flask 測試客戶端"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        # 在測試前設定一個乾淨的資料庫
        setup_test_database()
        yield client

def setup_test_database():
    """為測試建立一個包含假數據的資料庫"""
    db_path = Path(os.environ["DB_FILE"])
    if db_path.exists():
        db_path.unlink()

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    # 建立表
    cursor.execute("""
    CREATE TABLE status_table (
        id INTEGER PRIMARY KEY, current_stage TEXT, apps_status TEXT,
        action_url TEXT, cpu_usage REAL, ram_usage REAL
    )""")
    cursor.execute("""
    CREATE TABLE log_table (
        id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        level TEXT, message TEXT
    )""")
    # 插入假數據
    apps_status = json.dumps({"quant": "running", "transcriber": "pending"})
    cursor.execute(
        """
        INSERT INTO status_table (id, current_stage, apps_status, action_url, cpu_usage, ram_usage)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (1, 'running_apps', apps_status, 'http://fake.url', 15.5, 45.2)
    )
    cursor.execute("INSERT INTO log_table (level, message) VALUES (?, ?)", ('INFO', 'Test log 1'))
    cursor.execute("INSERT INTO log_table (level, message) VALUES (?, ?)", ('WARNING', 'Test log 2'))
    conn.commit()
    conn.close()

def test_get_status_success(client):
    """測試 /api/status 端點是否成功返回數據"""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['current_stage'] == 'running_apps'
    assert data['cpu_usage'] == 15.5
    assert json.loads(data['apps_status'])['quant'] == 'running'

def test_get_logs_success(client):
    """測試 /api/logs 端點是否成功返回日誌列表"""
    response = client.get('/api/logs')
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]['message'] == 'Test log 2' # 因為是 DESC 排序
    assert data[1]['level'] == 'INFO'

def test_get_status_no_data(client):
    """測試在沒有數據時 /api/status 是否返回 404"""
    # 刪除資料庫中的紀錄
    conn = sqlite3.connect(os.environ["DB_FILE"])
    conn.execute("DELETE FROM status_table")
    conn.commit()
    conn.close()

    response = client.get('/api/status')
    assert response.status_code == 404
    data = response.get_json()
    assert 'No status data found' in data['error']
