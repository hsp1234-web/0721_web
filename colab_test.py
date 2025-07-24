import sys
from unittest.mock import MagicMock

# --- 模擬 Colab 和 IPython 環境 ---
# 這是為了讓應用程式的核心邏輯可以在非 Colab 環境中運行，以便進行測試。
# 它會攔截對這些模組的導入請求，並返回一個模擬物件，
# 這樣就不會因為找不到模組而拋出 ImportError。

sys.modules['IPython'] = MagicMock()
sys.modules['IPython.display'] = MagicMock()
sys.modules['google.colab'] = MagicMock()
sys.modules['google.colab.output'] = MagicMock()
sys.modules['psutil'] = MagicMock()

# --- 啟動器 ---
# 這個啟動器會導入並執行主應用程式。
# 它是在 `colab_test.py` 成功模擬了必要的模組之後才被導入的。

import colab_run

def run_app():
    """
    設定應用的運行參數並啟動主函數。
    """
    # 從命令列參數獲取埠號，這是從 test.sh 傳遞過來的。
    if len(sys.argv) > 1:
        colab_run.FASTAPI_PORT = int(sys.argv[1])

    # 呼叫主應用程式的入口點。
    colab_run.main()

if __name__ == "__main__":
    run_app()
