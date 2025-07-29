# -*- coding: utf-8 -*-
"""
量化 App 的 API 測試
"""
import sys
from pathlib import Path

from fastapi.testclient import TestClient

from src.quant.main import app

# 使用 FastAPI 的測試客戶端
client = TestClient(app)

def test_health_check():
    """
    測試 `/api/v1/health` 端點是否正常工作。
    """
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "量化金融服務運行中"}

def test_root_path():
    """
    測試根路由 `/` 是否正常。
    """
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "歡迎來到量化金融服務 API"}

def test_perform_backtest_api(mocker):
    """
    測試 /v1/backtest API 端點。

    我們使用 pytest-mock 的 `mocker` 來模擬 (mock) 真正的業務邏輯函式，
    這樣我們就可以在不實際執行耗時計算或 API 呼叫的情況下，
    驗證 API 層的行為是否正確。
    """
    # 步驟 1: 準備模擬
    # 定義一個假的、成功的返回結果
    mock_success_result = {
        "stock_id": "2330.TW",
        "start_date": "2023-01-01",
        "end_date": "2024-01-01",
        "final_value": 120000.0,
        "total_return_pct": 20.0,
    }

    # 模擬 analysis.run_simple_backtest 函式，讓它總是返回我們的假結果
    mocker.patch(
        "src.quant.logic.analysis.run_simple_backtest",
        return_value=mock_success_result
    )

    # 模擬 database.db_manager.save_backtest_result 函式，因為我們不想真的寫入資料庫
    mock_db_save = mocker.patch("src.quant.logic.database.db_manager.save_backtest_result")

    # 步驟 2: 呼叫 API
    request_payload = {
        "stock_id": "2330.TW",
        "start_date": "2023-01-01",
        "end_date": "2024-01-01"
    }
    response = client.post("/api/v1/backtest", json=request_payload)

    # 步驟 3: 斷言結果
    # 驗證 API 是否返回 200 OK
    assert response.status_code == 200
    # 驗證 API 的回應是否就是我們模擬的結果
    assert response.json() == mock_success_result
    # 驗證資料庫儲存函式是否被呼叫了一次
    mock_db_save.assert_called_once_with(mock_success_result)

def test_perform_backtest_api_error(mocker):
    """
    測試當業務邏輯層返回錯誤時，API 是否能正確處理。
    """
    # 步驟 1: 準備模擬
    # 模擬業務邏輯函式返回一個包含錯誤訊息的字典
    mock_error_result = {"error": "模擬的數據獲取失敗"}
    mocker.patch(
        "src.quant.logic.analysis.run_simple_backtest",
        return_value=mock_error_result
    )

    # 步驟 2: 呼叫 API
    request_payload = {
        "stock_id": "FAKE.TW",
        "start_date": "2023-01-01",
        "end_date": "2024-01-01"
    }
    response = client.post("/api/v1/backtest", json=request_payload)

    # 步驟 3: 斷言結果
    # 驗證 API 是否返回 400 Bad Request
    assert response.status_code == 400
    # 驗證回應的詳細訊息是否就是我們模擬的錯誤訊息
    assert response.json() == {"detail": mock_error_result["error"]}
