import os
import sys
import time
from unittest.mock import MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.transcriber import logic as transcriber_logic
from main import app  # 載入 FastAPI 主應用


@pytest.fixture
def mock_load_model(monkeypatch):
    """替換掉真實的、耗時的 _load_model 函數。"""
    mock_model = {"version": "1.0-test", "load_time": time.time()}
    load_model_mock = MagicMock(return_value=mock_model)
    monkeypatch.setattr(transcriber_logic, "_load_model", load_model_mock)
    # 重置 AI_MODEL 狀態，確保每個測試都在乾淨的環境中運行
    monkeypatch.setattr(transcriber_logic, "AI_MODEL", None)
    return load_model_mock


@pytest_asyncio.fixture
async def client():
    """建立一個異步的 httpx client 來測試 app。"""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac


@pytest.mark.asyncio
async def test_transcriber_root(client: AsyncClient):
    """測試 transcriber 的根路由是否正常。"""
    response = await client.get("/transcriber/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "這裡是語音轉錄 (Transcriber) 服務，已準備好接收上傳。"
    }


@pytest.mark.asyncio
async def test_upload_invalid_content_type(client: AsyncClient):
    """測試上傳非音訊檔案時，是否返回 415 錯誤。"""
    files = {"file": ("test.txt", b"some text", "text/plain")}
    response = await client.post("/transcriber/upload", files=files)
    assert response.status_code == 415
    assert "不支援的檔案類型" in response.json()["detail"]


@pytest.mark.asyncio
async def test_lazy_loading_of_model(client: AsyncClient, mock_load_model: MagicMock):
    """測試懶加載邏輯是否按預期工作。"""
    # 第一次請求
    files = {"file": ("test.mp3", b"fake audio data", "audio/mpeg")}
    response = await client.post("/transcriber/upload", files=files)

    # 驗證第一次請求
    assert response.status_code == 200
    assert "transcription" in response.json()
    # 確認 _load_model 被呼叫了一次
    mock_load_model.assert_called_once()

    # --- 第二次請求 ---
    files2 = {"file": ("test2.wav", b"more fake audio", "audio/wav")}
    response2 = await client.post("/transcriber/upload", files=files2)

    # 驗證第二次請求
    assert response2.status_code == 200
    # 確認 _load_model 仍然只被呼叫了一次，沒有被再次呼叫
    mock_load_model.assert_called_once()
