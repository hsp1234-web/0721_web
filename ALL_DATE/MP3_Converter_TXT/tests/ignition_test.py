# 點火測試：確保核心服務能啟動且基礎 API 可回應
# 這個測試應該非常輕量，不應該導入任何需要額外大型依賴的模組

from fastapi.testclient import TestClient
from src.main import app  # 直接從 src.main 導入 app

# 檢查 TestClient 是否能成功掛載到 app
def test_test_client_creation():
    """驗證 TestClient 能否成功初始化"""
    with TestClient(app) as client:
        assert client is not None

# 檢查 /health 端點是否正常回應
def test_health_check():
    """驗證 /health 端點是否返回 {"status": "ok"}"""
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
