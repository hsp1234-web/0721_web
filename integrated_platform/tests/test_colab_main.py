# tests/test_colab_main.py
# 注意：此檔案的路徑是相對於專案根目錄的
import sys
from pathlib import Path
import pytest

# 將 colab_main.py 所在的目錄（專案根目錄）加入到 sys.path
# 這樣我們才能 'from colab_main import ...'
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# 現在我們可以安全地從 colab_main 導入
# 我們需要模擬 colab_main 中的一些全域變數和導入
from unittest.mock import MagicMock

# 在導入 colab_main 之前，偽裝它的依賴
sys.modules['google.colab'] = MagicMock()
sys.modules['IPython.display'] = MagicMock()

# 偽裝全域 log_manager
import colab_main
colab_main.log_manager = MagicMock()

from colab_main import create_public_portal

def test_create_portal_success(mocker):
    """
    測試案例：驗證在成功情況下，函式行為是否正確
    """
    # 1. 偽裝 (Mock) 所有外部依賴
    # 全域 log_manager 已經在檔案頂部被偽裝
    mock_log_manager = colab_main.log_manager

    # 從 sys.modules 中獲取偽裝的模組
    mock_display = sys.modules['IPython.display'].display
    mock_HTML = sys.modules['IPython.display'].HTML
    mock_colab_output = sys.modules['google.colab'].output

    # 偽裝 time.sleep 以加快測試速度
    mocker.patch('time.sleep')

    # 設定 colab_output 的返回值
    mock_colab_output.eval_js.return_value = "https://mock-url-from-colab.com"

    # 2. 執行待測函式
    create_public_portal(port=8000)

    # 3. 驗證 (Assert)
    # 驗證 Colab API 是否被正確呼叫
    mock_colab_output.serve_kernel_port_as_window.assert_called_once_with(8000, path='/')
    mock_colab_output.eval_js.assert_called_once_with("google.colab.kernel.proxyPort(8000)")

    # 驗證「漂亮按鈕」是否被顯示
    mock_display.assert_called_once()
    # 驗證傳遞給 HTML 的內容是否包含返回的 URL
    mock_HTML.assert_called_once_with(mocker.ANY)
    html_content_arg = mock_HTML.call_args[0][0]
    assert "https://mock-url-from-colab.com" in html_content_arg

    # 驗證日誌記錄
    # 初始日誌
    mock_log_manager.log.assert_any_call("INFO", "奉命建立服務入口...")
    # 成功日誌
    assert any(
        call.args[0] == "SUCCESS" and "服務入口已建立" in call.args[1]
        for call in mock_log_manager.log.call_args_list
    ), "應記錄 SUCCESS 日誌"


def test_create_portal_retry_and_fail(mocker):
    """
    測試案例：驗證在API持續失敗時，重試與最終失敗的邏輯
    """
    # 1. 偽裝依賴，並讓其中一個假人「假裝失敗」
    mock_log_manager = colab_main.log_manager
    mock_log_manager.reset_mock() # 重設 mock 以免受上個測試影響

    mock_sleep = mocker.patch('time.sleep')
    mock_colab_output = sys.modules['google.colab'].output
    mock_colab_output.reset_mock() # 重設 mock 以免受上個測試影響

    # 命令假人在被呼叫時，拋出一個異常
    mock_colab_output.serve_kernel_port_as_window.side_effect = Exception("模擬 API 失敗")

    # 2. 執行待測函式
    create_public_portal(retries=3, delay=2) # 測試時減少重試次數和延遲

    # 3. 驗證
    # 驗證 API 被呼叫了 3 次
    assert mock_colab_output.serve_kernel_port_as_window.call_count == 3

    # 驗證函式在每次失敗後都等待了
    # 3次失敗，中間等待2次
    assert mock_sleep.call_count == 2
    mock_sleep.assert_called_with(2) # 驗證等待時間是否正確

    # 驗證最終記錄了 CRITICAL 日誌
    # 使用 call_args 獲取最後一次呼叫的參數
    final_log_call = mock_log_manager.log.call_args
    assert final_log_call.args[0] == "CRITICAL"
    assert "所有建立公開服務入口的嘗試均告失敗" in final_log_call.args[1]

    # 驗證 WARNING 日誌被呼叫了 3 次
    warning_calls = [
        call for call in mock_log_manager.log.call_args_list
        if call.args[0] == 'WARNING'
    ]
    assert len(warning_calls) == 3
