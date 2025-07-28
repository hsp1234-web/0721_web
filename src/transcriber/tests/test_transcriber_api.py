# -*- coding: utf-8 -*-
"""
語音轉寫 App 的 API 點火測試
"""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# --- 設置導入路徑 ---
# 這一步至關重要，確保測試可以找到 App 的主模組
# 我們將 'apps' 目錄添加到 Python 路徑中
# 這樣 `from transcriber.main import app` 就能成功
app_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(app_dir))

from transcriber.main import app  # noqa: E402

# 使用 FastAPI 的測試客戶端
client = TestClient(app)

def test_health_check():
    """
    測試 `/health` 端點是否正常工作。
    這是一個最基本的「點火測試」，確認伺服器可以啟動並回應請求。
    """
    response = client.get("/health")
    # 斷言 HTTP 狀態碼為 200 (OK)
    assert response.status_code == 200
    # 斷言回應的 JSON 內容符合預期
    assert response.json() == {"status": "ok", "message": "語音轉寫服務運行中"}

def test_upload_without_file():
    """
    測試在沒有提供檔案的情況下呼叫 /upload 端點。
    FastAPI 會因為缺少必要的 `File` 部分而返回 422 錯誤。
    """
    # 當不提供 `files` 參數時，TestClient 會發送一個沒有 multipart/form-data 的請求
    response = client.post("/upload")
    # 斷言 HTTP 狀態碼為 422 Unprocessable Entity
    assert response.status_code == 422
    # 檢查 FastAPI 返回的標準驗證錯誤訊息
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["msg"] == "Field required"

def test_status_not_found():
    """
    測試查詢一個不存在的任務 ID。
    預期會收到 404 Not Found 錯誤。
    """
    non_existent_task_id = "a-fake-task-id"
    response = client.get(f"/status/{non_existent_task_id}")
    # 斷言 HTTP 狀態碼為 404
    assert response.status_code == 404
    # 斷言錯誤訊息
    assert response.json() == {"detail": f"找不到任務 ID: {non_existent_task_id}"}
