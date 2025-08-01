# -*- coding: utf-8 -*-
"""
此測試檔案專門用來驗證 `run` 目錄下的腳本是否可以被成功匯入。
這主要用來捕捉因為 `sys.path` 設定不正確而導致的 `ModuleNotFoundError`。
"""
import pytest

def test_import_colab_runner():
    """
    測試 `run/colab_runner.py` 是否可以被成功匯入。
    這會驗證 `sys.path` 是否被正確設定，讓它可以找到 `core_utils` 模組。
    """
    try:
        import run.colab_runner
        assert True
    except ImportError as e:
        # 在非 Colab 環境中，我們預期會缺少 'google' 或 'IPython' 模組。
        # 如果是這種情況，我們應該跳過測試，而不是將其標記為失敗。
        error_str = str(e).lower()
        if "no module named 'google'" in error_str or "no module named 'ipython'" in error_str:
            pytest.skip(f"跳過測試，因為缺少預期的 Colab/IPython 環境依賴: {e}")
        else:
            # 如果是任何其他匯入錯誤 (例如 'core_utils' 找不到)，則表示存在問題。
            pytest.fail(f"匯入 run.colab_runner 時發生非預期的 ImportError，這可能表示 sys.path 問題仍然存在: {e}", pytrace=False)
    except Exception as e:
        # 捕捉其他非匯入的意外錯誤
        pytest.fail(f"匯入 run.colab_runner 時發生非預期的錯誤: {e}")


def test_import_report_py():
    """
    測試 `run/report.py` 是否可以被成功匯入。
    這同樣驗證了 `sys.path` 的設定是否能讓它找到 `core_utils`。
    """
    try:
        import run.report
        # 如果匯入成功，我們就假設路徑問題已解決
        assert True
    except ImportError as e:
        pytest.fail(f"匯入 run.report 時發生錯誤，可能是 sys.path 問題未解決: {e}", pytrace=False)
    except Exception as e:
        if "No module named 'IPython'" in str(e):
             pytest.skip(f"跳過測試，因為缺少 IPython 環境依賴: {e}")
        else:
            pytest.fail(f"匯入 run.report 時發生非預期的錯誤: {e}")
