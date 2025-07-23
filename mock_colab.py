import sys
from unittest.mock import MagicMock
sys.modules['IPython'] = MagicMock()
sys.modules['IPython.display'] = MagicMock()
sys.modules['google.colab'] = MagicMock()
sys.modules['google.colab.output'] = MagicMock()
sys.modules['psutil'] = MagicMock()

from integrated_platform.src import colab_bootstrap
colab_bootstrap.FASTAPI_PORT = int(sys.argv[1])
colab_bootstrap.main()
