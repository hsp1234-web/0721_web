from fastapi.testclient import TestClient
from src.main import app # 從 src/main.py 導入 app
import io

# 建立一個測試客戶端
client = TestClient(app)

def test_read_root():
    """測試根目錄 (/) 是否成功回傳 HTML。"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "應用程式儀表板" in response.text

import pytest

@pytest.mark.smoke
def test_get_applications():
    """測試 /api/apps 是否回傳正確的 JSON 結構與內容。"""
    response = client.get("/api/apps")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 # 確保至少有兩個應用
    # 檢查第一個應用的鍵是否存在
    assert "id" in data[0]
    assert "name" in data[0]
    assert "icon" in data[0]
    assert "description" in data[0]

def test_upload_transcription_file():
    """測試檔案上傳與模擬轉寫功能。"""
    # 建立一個假的記憶體內檔案
    fake_audio_content = b"this is a fake audio file content"
    fake_file = ("test_audio.mp3", io.BytesIO(fake_audio_content), "audio/mpeg")

    response = client.post(
        "/api/transcribe/upload",
        files={"audio_file": fake_file}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_audio.mp3"
    assert "模擬語音轉寫結果" in data["transcription"]
