# -*- coding: utf-8 -*-
"""
語音轉寫 App 的端對端 API 測試 (v5 - 終極隔離模式)
"""
import sys
from pathlib import Path
from fastapi.testclient import TestClient

from src.transcriber import logic
from src.transcriber.main import app

TEST_AUDIO_PATH = Path(__file__).parent / "test_audio.wav"

def test_full_transcription_flow():
    """
    測試完整的轉寫流程，使用局部 client 和清晰的依賴覆寫。
    """
    # --- 步驟 1: 設定 Overrides ---
    # 在建立 TestClient 之前，先設定好這個測試專用的依賴覆寫
    def mock_process_audio_file(file):
        return "mock_task_id"

    def mock_get_task_status(task_id: str):
        return {"status": "completed", "transcript": "來自 override 的模擬結果"}

    app.dependency_overrides = {
        logic.process_audio_file: mock_process_audio_file,
        logic.get_task_status: mock_get_task_status,
    }

    # --- 步驟 2: 建立局部 Client ---
    # 這個 client 只在這個測試函式中存在，並且會使用上面設定的 overrides
    client = TestClient(app)

    # --- 步驟 3: 上傳音檔 ---
    assert TEST_AUDIO_PATH.exists()
    with open(TEST_AUDIO_PATH, "rb") as audio_file:
        response = client.post("/upload", files={"file": ("test_audio.wav", audio_file, "audio/wav")})

    # --- 步驟 4: 驗證上傳回應 ---
    assert response.status_code == 202
    task_id = response.json()["task_id"]
    assert task_id == "mock_task_id"

    # --- 步驟 5: 查詢狀態 ---
    status_response = client.get(f"/status/{task_id}")

    # --- 步驟 6: 驗證最終結果 ---
    assert status_response.status_code == 200
    assert status_response.json() == {"status": "completed", "transcript": "來自 override 的模擬結果"}

    # --- 步驟 7: 清理 ---
    # 清空 overrides，確保不影響任何其他可能的測試
    app.dependency_overrides = {}
