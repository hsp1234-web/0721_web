# -*- coding: utf-8 -*-
"""
語音轉寫 App 的 API 點火測試 (v4 - 終極隔離模式)
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

from src.transcriber.main import app

def test_health_check():
    """
    測試 `/health` 端點是否正常工作。
    """
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "語音轉寫服務運行中"}

def test_upload_without_file():
    """
    測試在沒有提供檔案的情況下呼叫 /upload 端點。
    """
    client = TestClient(app)
    response = client.post("/upload")
    assert response.status_code == 422

def test_status_not_found():
    """
    測試查詢一個不存在的任務 ID 的原始行為。
    """
    # --- 設定 ---
    # 為這個測試建立一個全新的、乾淨的 client
    # 確保沒有任何來自其他測試的依賴覆寫
    app.dependency_overrides = {}
    client = TestClient(app)

    # --- 執行 ---
    non_existent_task_id = "a-truly-fake-task-id"
    response = client.get(f"/status/{non_existent_task_id}")

    # --- 斷言 ---
    assert response.status_code == 404
    assert response.json() == {"detail": f"找不到任務 ID: {non_existent_task_id}"}
