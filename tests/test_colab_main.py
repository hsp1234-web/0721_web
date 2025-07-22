# --- 測試腳本 (tests/test_colab_main.py) ---

# 假設 create_public_portal 在 'src.colab_main' 模組中
from src.colab_main import create_public_portal

def test_create_portal_success(mocker):
    """
    測試案例：驗證在成功情況下，函式行為是否正確
    """
    # 1. 偽裝 (Mock) 所有外部依賴
    mock_log_manager = mocker.patch('colab_main.log_manager')
    mock_display = mocker.patch('colab_main.display')
    mock_colab_output = mocker.patch('colab_main.colab_output')
    mocker.patch('colab_main.time.sleep') # 確保測試不需等待

    # 2. 執行待測函式
    create_public_portal(mock_log_manager)

    # 3. 驗證 (Assert)
    # 驗證 Colab API 是否被正確呼叫
    mock_colab_output.eval_js.assert_called_once_with('google.colab.kernel.proxyPort(8000)')
    # 驗證「漂亮按鈕」是否被顯示
    mock_display.assert_called_once()
    # 驗證是否記錄了 SUCCESS 日誌
    # (可檢查 mock_log_manager.log.call_args)
    assert "SUCCESS" in mock_log_manager.log.call_args.args

def test_create_portal_retry_and_fail(mocker):
    """
    測試案例：驗證在API持續失敗時，重試與最終失敗的邏輯
    """
    # 1. 偽裝依賴，並讓其中一個假人「假裝失敗」
    mock_log_manager = mocker.patch('colab_main.log_manager')
    mock_sleep = mocker.patch('colab_main.time.sleep')
    mock_colab_output = mocker.patch('colab_main.colab_output')
    # 命令假人在被呼叫時，拋出一個異常
    mock_colab_output.eval_js.side_effect = Exception("模擬 API 失敗")

    # 2. 執行待測函式
    create_public_portal(mock_log_manager, retries=3) # 測試時可減少重試次數

    # 3. 驗證
    # 驗證 API 被呼叫了 3 次
    assert mock_colab_output.eval_js.call_count == 3
    # 驗證函式在每次失敗後都等待了
    assert mock_sleep.call_count == 2 # 3次失敗，中間等待2次
    # 驗證最終記錄了 CRITICAL 日誌
    assert "CRITICAL" in mock_log_manager.log.call_args.args
