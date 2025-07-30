# -*- coding: utf-8 -*-
import unittest
import subprocess
import sys
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

class TestColabSimulation(unittest.TestCase):
    def setUp(self):
        # 模擬 google.colab 模組
        self.google_mock = MagicMock()
        self.google_colab_mock = MagicMock()
        self.google_colab_output_mock = MagicMock()
        self.google_colab_output_mock.eval_js.return_value = "https://colab.research.google.com/proxy/8080/"

        sys.modules['google'] = self.google_mock
        sys.modules['google.colab'] = self.google_colab_mock
        sys.modules['google.colab.output'] = self.google_colab_output_mock

    def tearDown(self):
        # 清理模擬的模組
        del sys.modules['google']
        del sys.modules['google.colab']
        del sys.modules['google.colab.output']

    @patch('run.colab_runner.IS_COLAB', True)
    @patch('run.colab_runner.display')
    def test_colab_full_flow_simulation(self, mock_display):
        """
        模擬 Colab 環境下的完整端到端流程
        """
        # 1. 準備環境
        # 將 PROJECT_FOLDER_NAME 設定為一個臨時目錄
        # Correcting the path to be relative to the project root
        test_project_path = PROJECT_ROOT / "test_colab_project"
        if test_project_path.exists():
            subprocess.run(['rm', '-rf', str(test_project_path)])

        # 2. 模擬 `colab_runner.py` 的核心邏輯
        from run import colab_runner

        # 覆寫 base_path 以使用臨時目錄
        colab_runner.base_path = test_project_path.parent

        # 覆寫常數以進行測試
        colab_runner.PROJECT_FOLDER_NAME = str(test_project_path.name)
        colab_runner.FORCE_REPO_REFRESH = True
        colab_runner.RUN_MODE = "快速驗證模式 (Fast-Test Mode)"

        try:
            # 執行 main 函數
            colab_runner.main()
        except RuntimeError as e:
            # 預期會因為健康檢查失敗而引發 RuntimeError
            self.assertIn("後端服務啟動失敗", str(e))
        except Exception as e:
            self.fail(f"測試引發了未預期的例外：{e}")
        finally:
            # 3. 清理環境
            if test_project_path.exists():
                subprocess.run(['rm', '-rf', str(test_project_path)])

if __name__ == '__main__':
    unittest.main()
