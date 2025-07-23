# tests/test_colab_main.py
import sys
from unittest.mock import MagicMock

# --- 模擬 Colab 和 IPython 的模組 ---
sys.modules['google'] = MagicMock()
sys.modules['google.colab'] = MagicMock()
sys.modules['google.colab.output'] = MagicMock()
sys.modules['IPython'] = MagicMock()
sys.modules['IPython.display'] = MagicMock()
sys.modules['IPython.core.display'] = MagicMock()
sys.modules['ipywidgets'] = MagicMock()


from pathlib import Path
from integrated_platform.src.colab.colab_manager import ColabManager
from integrated_platform.src.log_manager import LogManager
from google.colab import output as mock_colab_output
from IPython.display import display as mock_display

# --- 測試案例 ---

def test_create_portal_success(mocker):
    """
    測試案例：驗證在成功情況下，函式行為是否正確
    """
    # 1. 重設我們的假人 (Mocks) 狀態，確保測試之間是隔離的
    mock_colab_output.reset_mock()
    mock_display.reset_mock()
    # 我們也需要偽裝 log_manager 和 time.sleep
    log_manager = LogManager(Path("test_logs.sqlite"))
    mocker.patch.object(log_manager, 'log')
    mocker.patch('time.sleep')
    mock_colab_output.serve_kernel_port_as_window.side_effect = None


    # 2. 執行待測函式
    colab_manager = ColabManager(log_manager)
    colab_manager.create_public_portal()

    # 3. 驗證 (Assert)
    # 驗證 Colab API 是否被正確呼叫
    mock_colab_output.serve_kernel_port_as_window.assert_called_once_with(8000, path="/")

    # 驗證「漂亮按鈕」是否被顯示
    mock_display.assert_called_once()

    # 驗證是否記錄了 SUCCESS 日誌
    # 我們可以檢查 log_manager.log 的最後一次呼叫
    final_log_call = log_manager.log.call_args
    assert "SUCCESS" in final_log_call.args[0]
    assert "服務入口已建立" in final_log_call.args[1]


def test_create_portal_retry_and_fail(mocker):
    """
    測試案例：驗證在API持續失敗時，重試與最終失敗的邏輯
    """
    # 1. 偽裝依賴，並讓其中一個假人「假裝失敗」
    mock_colab_output.reset_mock()
    mock_display.reset_mock()
    log_manager = LogManager(Path("test_logs.sqlite"))
    mock_log = mocker.patch.object(log_manager, 'log')
    mock_sleep = mocker.patch('time.sleep')

    # 命令假人在被呼叫時，拋出一個異常
    mock_colab_output.serve_kernel_port_as_window.side_effect = Exception("模擬 API 失敗")

    # 2. 執行待測函式
    colab_manager = ColabManager(log_manager)
    colab_manager.create_public_portal(retries=3, delay=5) # 測試時使用不同的參數

    # 3. 驗證
    # 驗證 API 被呼叫了 3 次
    assert mock_colab_output.serve_kernel_port_as_window.call_count == 3

    # 驗證函式在每次失敗後都等待了
    # 3次嘗試，意味著有2次失敗後的等待
    assert mock_sleep.call_count == 2
    # 驗證等待時間是正確的
    mock_sleep.assert_called_with(5)

    # 驗證最終記錄了 CRITICAL 日誌
    final_log_call = mock_log.call_args
    assert "CRITICAL" in final_log_call.args[0]
    assert "所有建立公開服務入口的嘗試均失敗" in final_log_call.args[1]

    # 驗證 display 沒有被呼叫，因為從未成功
    mock_display.assert_not_called()
