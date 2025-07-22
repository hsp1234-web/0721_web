import sys
from unittest.mock import MagicMock
import importlib

# --- 模擬 Colab 和 IPython 的模組 ---
sys.modules['google'] = MagicMock()
sys.modules['google.colab'] = MagicMock()
sys.modules['google.colab.output'] = MagicMock()
sys.modules['IPython'] = MagicMock()
sys.modules['IPython.display'] = MagicMock()
sys.modules['IPython.core.display'] = MagicMock()
sys.modules['ipywidgets'] = MagicMock()

import colab_main
importlib.reload(colab_main)

if __name__ == "__main__":
    colab_main.main()
