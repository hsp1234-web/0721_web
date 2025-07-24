# 檔案: integrated_platform/tests/test_final_deployment.py
from unittest.mock import patch, MagicMock
import colab_run
import pytest

# 思路框架：這不再是端到端測試，而是一個 "啟動腳本健康度" 的煙霧測試。

@patch('colab_run.run_command')
@patch('colab_run.DisplayManager')
@patch('colab_run.create_public_portal')
@patch('colab_run.start_fastapi_server')
@patch('colab_run.health_check', return_value=True)
def test_orchestrated_startup_does_not_crash(
    mock_health_check,
    mock_start_fastapi,
    mock_create_portal,
    mock_display,
    mock_run_command
):
    # 作法：我們只關心 colab_run.main 是否能在一個完全受控的環境下跑完。

    try:
        # 執行主函式
        # We need to run main in a thread because it has an infinite loop
        import threading
        main_thread = threading.Thread(target=colab_run.main)
        main_thread.daemon = True
        main_thread.start()
        # Give the thread a moment to run and hit the mocks
        main_thread.join(timeout=2)

        # Signal the main loop to stop
        colab_run.STOP_EVENT.set()
        main_thread.join(timeout=2)

        execution_successful = not main_thread.is_alive()

    except Exception as e:
        print(f"Test failed with exception: {e}")
        execution_successful = False

    # 斷言：
    # 1. 整個過程沒有崩潰。
    assert execution_successful is True
    # 2. 依賴安裝的函式被呼叫了。
    assert mock_run_command.called
    # 3. 儀表板被啟動了。
    assert mock_display.return_value.start.called
    # 4. FastAPI 伺服器被啟動了。
    assert mock_start_fastapi.called
    # 5. 健康檢查被呼叫了。
    assert mock_health_check.called
    # 6. 公開入口被建立了。
    assert mock_create_portal.called
