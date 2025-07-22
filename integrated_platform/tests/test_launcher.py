# 測試啟動器、伺服器生命週期和 API 契約的整合測試
# tests/test_launcher.py

import pytest
import threading
import time
import httpx
import uvicorn
from unittest.mock import MagicMock, patch

# 匯入我們要測試的目標
from integrated_platform.src.main import app
import colab_main

# --- 常數設定 ---
HOST = "127.0.0.1"
PORT = 8000
BASE_URL = f"http://{HOST}:{PORT}"


# --- Fixtures ---

@pytest.fixture(scope="module")
def live_server():
    """
    【生命週期管理器 Fixture】
    在測試模組執行前，於背景啟動一個真實的 FastAPI 伺服器，
    並在所有測試結束後將其關閉。
    """
    # 1. 定義一個函式，用於在 uvicorn 中運行 app
    #    由於 uvicorn.run() 會阻塞，我們需要一個 flag 來控制它何時停止
    server_started = threading.Event()

    def run_server():
        config = uvicorn.Config(app, host=HOST, port=PORT, log_level="info")
        server = uvicorn.Server(config)

        # 綁定伺服器啟動完成事件
        original_startup = server.startup
        async def new_startup():
            await original_startup()
            server_started.set() # 通知主執行緒伺服器已啟動
        server.startup = new_startup

        server.run()

    # 2. 建立並啟動一個背景執行緒來運行 run_server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # 3. 等待伺服器完全啟動
    server_started.wait(timeout=5)

    # 4. 使用 yield 將控制權交還給測試函式
    yield BASE_URL

    # 5. 測試結束後，執行清理邏輯
    #    因為執行緒是 daemon，它會隨主進程結束，uvicorn 會自動清理
    print("\nLive server tests finished.")


# --- 測試案例 ---

def test_api_health_check(live_server):
    """
    【API 契約測試】
    驗證「活的」伺服器根端點 (/) 是否正常。
    """
    try:
        # 1. 向健康檢查端點發送 GET 請求
        response = requests.get(live_server, timeout=5)

        # 2. 驗證回應
        assert response.status_code == 200
        assert "<h1>鳳凰轉錄儀</h1>" in response.text

    except requests.ConnectionError as e:
        pytest.fail(f"無法連接到即時伺服器: {e}")


@patch('colab_main.create_public_portal', return_value=None)
@patch('colab_main.DisplayManager')
@patch('colab_main.subprocess.Popen')
def test_launcher_starts_uvicorn_successfully(mock_popen, mock_display_manager, mock_create_portal):
    """
    【調度邏輯測試 - 成功場景】
    驗證 colab_main.py 是否正確地呼叫了 uvicorn。
    """
    # 1. 偽裝 subprocess.Popen
    mock_process = MagicMock()
    # 第一次 poll 回傳 None (執行中)，之後回傳 0 (正常結束)
    mock_process.poll.side_effect = [None, 0]
    mock_process.stdout.readline.return_value = '' # 模擬日誌流結束
    mock_popen.return_value = mock_process

    # 2. 執行指揮中心的核心啟動函式
    #    使用 try...except KeyboardInterrupt 來模擬正常執行直到手動停止
    try:
        colab_main.main()
    except KeyboardInterrupt:
        pass # 這是預期的退出方式

    # 3. 驗證
    #    - 驗證 Popen 是否以正確的命令被呼叫
    mock_popen.assert_called_once()
    args, kwargs = mock_popen.call_args
    expected_command_start = ["poetry", "run", "uvicorn", "src.main:app"]
    assert args[0][:4] == expected_command_start

    #    - 驗證建立了服務入口
    mock_create_portal.assert_called_once()


@patch('colab_main.create_public_portal', return_value=None)
@patch('colab_main.DisplayManager')
@patch('colab_main.log_manager.log')
@patch('colab_main.subprocess.Popen')
def test_launcher_handles_subprocess_failure(mock_popen, mock_log, mock_display_manager, mock_create_portal):
    """
    【調度邏輯測試 - 失敗場景】
    驗證啟動 uvicorn 失敗時，Python 指揮中心是否會捕獲錯誤並記錄。
    """
    # 1. 偽裝 subprocess.Popen，讓它在被呼叫時就拋出錯誤
    mock_popen.side_effect = OSError("Mocker: command not found")

    # 2. 執行指揮中心的核心啟動函式
    colab_main.main()

    # 3. 驗證是否記錄了嚴重錯誤
    #    我們預期 CRITICAL 級別的日誌被呼叫，且訊息包含我們拋出的錯誤
    critical_call_found = False
    for call in mock_log.call_args_list:
        args, kwargs = call
        if args[0] == "CRITICAL":
            assert "Mocker: command not found" in args[1]
            critical_call_found = True
            break

    assert critical_call_found, "未找到預期的 CRITICAL 日誌"
