# -*- coding: utf-8 -*-
import pytest
import subprocess
import time
import httpx
import sys
from pathlib import Path

# 為儀表板應用撰寫端對端測試

# 定義一個 fixture，用於在測試開始前啟動 launch.py，並在測試結束後終止它
@pytest.fixture(scope="module")
def live_server(): # 移除 full_mode_config 來啟用 launch.py 的預設快速模式
    """
    以快速模式啟動後端服務 (`launch.py`)，用於測試核心 API 通訊。
    'module' 範圍意味著對於此檔案中的所有測試，伺服器只會啟動一次。
    """
    process = None
    db_path = Path("logs/e2e_dashboard_test.db")
    # 清理舊的日誌
    if db_path.exists():
        db_path.unlink()
    # 在快速模式下，我們不需要清理 venv，因為根本不會建立它們

    try:
        # 使用 subprocess.Popen 在背景啟動 launch.py
        # launch.py 在沒有 FAST_TEST_MODE: False 的情況下，預設進入快速模式
        command = [sys.executable, "launch.py", "--db-file", str(db_path)]

        with open("logs/e2e_test_server.log", "w") as log_file:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                encoding='utf-8'
            )

        # 在快速模式下，服務應該很快就緒，但我們輪詢的是 API 端口 8088
        max_wait = 60  # 縮短等待時間至 60 秒
        start_time = time.time()
        is_ready = False
        api_url = "http://localhost:8088/api/v1/status"
        while time.time() - start_time < max_wait:
            try:
                with httpx.Client() as client:
                    # 我們輪詢的是後端狀態 API，而不是主儀表板
                    response = client.get(api_url)
                    if response.status_code == 200:
                        is_ready = True
                        break
            except httpx.ConnectError:
                time.sleep(1) # 縮短輪詢間隔

        if not is_ready:
            raise RuntimeError(f"E2E 測試的後端 API 在 {max_wait} 秒內未能啟動。")

        yield # 將控制權交給測試

    finally:
        if process:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()

@pytest.mark.e2e
def test_main_dashboard_loads_successfully(live_server):
    """
    一個簡單的 E2E 測試，驗證後端狀態 API 是否能成功回應。
    """
    # 在快速模式下，我們測試的是後端 API (port 8088)，而不是前端 UI (port 8000)
    url = "http://localhost:8088/api/v1/status"
    try:
        with httpx.Client() as client:
            response = client.get(url)

        assert response.status_code == 200, f"預期狀態碼為 200，但收到 {response.status_code}"

        # 驗證回應是否為有效的 JSON
        data = response.json()
        assert "status" in data, "API 回應中缺少 'status' 鍵"
        assert "logs" in data, "API 回應中缺少 'logs' 鍵"
        assert "performance_history" in data, "API 回應中缺少 'performance_history' 鍵"

    except httpx.RequestError as e:
        pytest.fail(f"向後端狀態 API ({url}) 發送請求時發生錯誤: {e}")
    except Exception as e:
        pytest.fail(f"處理 API 回應時發生非預期錯誤: {e}")
