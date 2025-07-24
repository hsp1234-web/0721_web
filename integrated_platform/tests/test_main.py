from fastapi.testclient import TestClient
from integrated_platform.src.main import app
import io
import pytest

# 思路框架：這是最純粹的 API 邏輯測試，不涉及任何外部進程或環境模擬。

def test_health_check():
    """測試 /health 健康檢查端點。"""
    # 作法：使用 with 陳述式確保 lifespan 事件被觸發。
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        # 根據 main.py 的定義，回傳的 JSON 應該包含 status: ok
        assert response.json()["status"] == "ok"

def test_read_root():
    """測試根目錄 (/) 是否成功回傳 HTML。"""
    with TestClient(app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]
        assert "應用程式儀表板" in response.text

@pytest.mark.smoke
def test_get_applications():
    """測試 /api/apps 是否回傳正確的 JSON 結構與內容。"""
    with TestClient(app) as client:
        response = client.get("/api/apps")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2
        assert "id" in data[0]
        assert "name" in data[0]
        assert "icon" in data[0]
        assert "description" in data[0]

def test_upload_audio_file():
    """測試檔案上傳與模擬轉寫功能。"""
    with TestClient(app) as client:
        # 準備一個模擬的檔案上傳
        fake_audio_content = b"this is a fake audio file content"
        # 修正 files 字典的鍵為 'file'，以匹配 main.py 中的 `File(...)`
        files = {'file': ('test_audio.mp3', io.BytesIO(fake_audio_content), 'audio/mpeg')}

        # 修正端點為 /upload
        response = client.post("/upload", files=files)

        # 斷言：首先確保路由存在 (非 404)，然後再驗證邏輯。
        assert response.status_code != 404
        assert response.status_code == 200

        # 驗證回傳的 JSON 內容
        data = response.json()
        assert "task_id" in data
        assert data["message"] == "檔案已上傳，轉寫任務已啟動。"
