# -*- coding: utf-8 -*-
import pytest
import subprocess
import time
import httpx
import sys
import os

# 為儀表板應用撰寫端對端測試

# 定義一個 fixture，用於在測試開始前啟動 launch.py --full，並在測試結束後終止它
@pytest.fixture(scope="module")
def live_server():
    """
    啟動一個完整的後端服務實例，包括所有應用程式。
    'module' 範圍意味著對於此檔案中的所有測試，伺服器只會啟動一次。
    """
    process = None
    try:
        # 使用 subprocess.Popen 在背景啟動 launch.py
        # 我們傳遞 --full 旗標來確保所有服務都被安裝和啟動
        command = [sys.executable, "launch.py", "--full"]
        # 將所有輸出重定向到一個日誌檔案中，以便於除錯
        with open("logs/e2e_test_server.log", "w") as log_file:
            process = subprocess.Popen(
                command,
                stdout=log_file,
                stderr=subprocess.STDOUT,
                encoding='utf-8'
            )

        # 等待伺服器啟動。我們需要一個可靠的方式來知道伺服器何時就緒。
        # 在這裡，我們輪詢主儀表板的端口 (8000)。
        max_wait = 300  # 最長等待 5 分鐘
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
                time.sleep(5) # 伺服器尚未就緒，稍後重試

        if not is_ready:
            raise RuntimeError("E2E 測試的後端服務在 5 分鐘內未能啟動。")

        # 當伺服器就緒時，將控制權交給測試函數
        yield

    finally:
        # 測試結束後，無論成功或失敗，都確保終止後端服務進程
        if process:
            process.terminate()
            try:
                process.wait(timeout=10) # 等待最多 10 秒讓它正常關閉
            except subprocess.TimeoutExpired:
                process.kill() # 如果無法正常關閉，則強制終結

@pytest.mark.e2e
def test_main_dashboard_loads_successfully(live_server):
    """
    一個簡單的 E2E 測試，驗證主儀表板是否能成功載入。
    """
    url = "http://localhost:8000/"
    try:
        with httpx.Client() as client:
            response = client.get(url)

        # 斷言 1: HTTP 狀態碼應該是 200 (OK)
        assert response.status_code == 200, f"預期狀態碼為 200，但收到 {response.status_code}"

        # 斷言 2: 回應的 HTML 內容中應該包含關鍵字
        # 我們從 `control_panel.html` 中找一個獨特的字串
        assert "鳳凰之心指揮中心" in response.text, "回應的 HTML 中未找到'鳳凰之心指揮中心'關鍵字"

    except httpx.RequestError as e:
        pytest.fail(f"向主儀表板 ({url}) 發送請求時發生錯誤: {e}")
