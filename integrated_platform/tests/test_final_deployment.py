# 檔案: integrated_platform/tests/test_final_deployment.py
# P8 架構下的新測試
from unittest.mock import patch, MagicMock
import threading
import time
import pytest

# 待測模組
import colab_run

# 思路框架：
# 驗證 Colab 啟動器 (colab_run.py) 與核心引擎 (core_run.py) 之間的協作是否正確。
# 我們需要驗證 colab_run.main() 是否會：
# 1. 在背景線程中啟動 core_run.main()。
# 2. 啟動並運行 DisplayManager。
# 3. 嘗試建立公開入口。

@patch('colab_run.start_core_engine_in_background')
@patch('colab_run.DisplayManager')
@patch('colab_run.create_public_portal')
@patch('time.sleep') # Mock time.sleep to speed up the test
def test_colab_launches_core_and_ui(mock_sleep, mock_create_portal, mock_display_manager, mock_start_core_engine):
    """
    測試 colab_run.main 是否能正確啟動核心引擎和 UI 管理器。
    """
    # --- 準備 ---
    # 創建一個 mock 的 thread 對象，並讓 is_alive() 在幾次調用後返回 False，以終止 main() 中的循環
    mock_thread = MagicMock()
    mock_thread.is_alive.side_effect = [True, True, False]
    mock_start_core_engine.return_value = mock_thread

    # --- 執行 ---
    try:
        colab_run.main()

        # --- 驗證 ---
        # 1. 斷言核心引擎的啟動函式被呼叫了一次
        mock_start_core_engine.assert_called_once()

        # 2. 斷言 DisplayManager 被實例化並啟動
        mock_display_manager.assert_called_once()
        mock_display_manager.return_value.setup_ui.assert_called_once()
        mock_display_manager.return_value.start.assert_called_once()

        # 3. 斷言建立公開入口的函式被呼叫
        mock_create_portal.assert_called_once()

    finally:
        # 確保在測試結束時重置 STOP_EVENT
        colab_run.STOP_EVENT.clear()
