# -*- coding: utf-8 -*-
import pytest
import subprocess
import time
import httpx
import sys
import os
import shutil
from pathlib import Path

# 為儀表板應用撰寫端對端測試

# 定義一個 fixture，用於在測試開始前啟動 launch.py，並在測試結束後終止它
@pytest.fixture(scope="module")
def live_server(full_mode_config): # 使用來自 conftest.py 的共享 fixture
    """
    啟動一個完整的後端服務實例，包括所有應用程式。
    'module' 範圍意味著對於此檔案中的所有測試，伺服器只會啟動一次。
    """
    process = None
    # 清理舊的日誌和 venv
    for app_dir in ["apps/main_dashboard", "apps/quant", "apps/transcriber"]:
        venv_path = Path(app_dir) / ".venv"
        if venv_path.exists():
            shutil.rmtree(venv_path, ignore_errors=True)
    if Path("logs/e2e_dashboard_test.db").exists():
        Path("logs/e2e_dashboard_test.db").unlink()

    try:
        # 使用 subprocess.Popen 在背景啟動 launch.py
        command = [sys.executable, "launch.py", "--db-file", "logs/e2e_dashboard_test.db"]

        with open("logs/e2e_test_server.log", "w") as log_file:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                encoding='utf-8'
            )

        # 等待伺服器啟動 (輪詢主儀表板的端口 8000)
        max_wait = 600  # 延長等待時間到 10 分鐘
        start_time = time.time()
        is_ready = False
        while time.time() - start_time < max_wait:
            try:
                with httpx.Client() as client:
                    response = client.get("http://localhost:8000")
                    if response.status_code == 200:
                        is_ready = True
                        break
            except httpx.ConnectError:
                time.sleep(5)

        if not is_ready:
            raise RuntimeError(f"E2E 測試的後端服務在 {max_wait} 秒內未能啟動。")

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
    一個簡單的 E2E 測試，驗證主儀表板是否能成功載入。
    """
    url = "http://localhost:8000/"
    try:
        with httpx.Client() as client:
            response = client.get(url)

        assert response.status_code == 200, f"預期狀態碼為 200，但收到 {response.status_code}"

        assert "鳳凰之心指揮中心" in response.text, "回應的 HTML 中未找到'鳳凰之心指揮中心'關鍵字"

    except httpx.RequestError as e:
        pytest.fail(f"向主儀表板 ({url}) 發送請求時發生錯誤: {e}")
