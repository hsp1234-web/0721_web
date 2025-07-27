import pytest
from fastapi.testclient import TestClient

# 這裡我們假設 transcriber 的 main.py 中有一個 app 物件
# 在實際的獨立插件架構中，我們會從插件的某個地方導入 router
# 但目前我們先假設它存在於 main.py
try:
    from apps.transcriber.main import app
    client = TestClient(app)
    TRANSCRIBER_APP_AVAILABLE = True
except (ImportError, AttributeError):
    TRANSCRIBER_APP_AVAILABLE = False


@pytest.mark.skipif(not TRANSCRIBER_APP_AVAILABLE, reason="Transcriber app or its router not found")
def test_transcriber_health_check():
    """
    測試轉錄插件是否有一個健康檢查端點。
    這是一個假設，實際端點可能不同。
    """
    # 假設轉錄插件在 /transcriber/health 路徑下提供健康檢查
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
