# -*- coding: utf-8 -*-
import unittest
import subprocess
import sys
import os
import json
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from run import colab_runner
from core_utils import safe_installer, resource_monitor

class TestColabFullSimulation(unittest.TestCase):

    def setUp(self):
        self.test_project_path = PROJECT_ROOT / "test_colab_project_real"
        if self.test_project_path.exists():
            subprocess.run(['rm', '-rf', str(self.test_project_path)])
        self.test_project_path.mkdir()

        colab_runner.base_path = self.test_project_path.parent
        colab_runner.PROJECT_FOLDER_NAME = self.test_project_path.name
        colab_runner.FORCE_REPO_REFRESH = True
        colab_runner.RUN_MODE = "完整部署模式 (Full-Deploy Mode)"

        # 模擬 google.colab 模組
        self.google_mock = MagicMock()
        self.google_colab_mock = MagicMock()
        self.google_colab_output_mock = MagicMock()
        self.google_colab_output_mock.eval_js.return_value = "https://colab.research.google.com/proxy/8080/"

        sys.modules['google'] = self.google_mock
        sys.modules['google.colab'] = self.google_colab_mock
        sys.modules['google.colab.output'] = self.google_colab_output_mock

    def tearDown(self):
        if self.test_project_path.exists():
            subprocess.run(['rm', '-rf', str(self.test_project_path)])
        del sys.modules['google']
        del sys.modules['google.colab']
        del sys.modules['google.colab.output']

    def test_full_system_flow(self):
        # 1. 啟動 colab_runner
        runner_process = subprocess.Popen([sys.executable, str(PROJECT_ROOT / "run" / "colab_runner.py")],
                                          cwd=self.test_project_path)

        # 2. 等待後端服務啟動 (帶重試機制的健康檢查)
        max_retries = 12
        retry_interval = 5
        for i in range(max_retries):
            try:
                response = httpx.get("http://localhost:8080/api/health")
                if response.status_code == 200:
                    break
            except httpx.ConnectError:
                pass
            time.sleep(retry_interval)
        else:
            self.fail("後端服務在指定時間內未啟動")

        # 3. 驗證後端服務是否正常
        response = httpx.get("http://localhost:8080/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok"})

        # 4. 模擬儀表板更新
        response = httpx.get("http://localhost:8080/api/status")
        self.assertEqual(response.status_code, 200)
        status_data = response.json()
        self.assertIn("current_stage", status_data)
        self.assertIn("apps_status", status_data)

        # 5. 驗證 App 功能
        # (此處可以新增對各個 App API 的呼叫，以驗證其功能)

        # 6. 停止 runner
        runner_process.terminate()
        runner_process.wait()

    @patch('core_utils.resource_monitor.is_resource_sufficient')
    def test_safe_installer_logic(self, mock_is_resource_sufficient):
        # 模擬資源充足
        mock_is_resource_sufficient.return_value = (True, "OK")
        with open("dummy_requirements.txt", "w") as f:
            f.write("requests\n")

        with patch('subprocess.run') as mock_subprocess_run:
            safe_installer.install_packages(
                app_name="test_app",
                requirements_path="dummy_requirements.txt",
                python_executable="python"
            )
            mock_subprocess_run.assert_called()

        # 模擬資源不足
        mock_is_resource_sufficient.return_value = (False, "FAIL")
        with self.assertRaises(SystemExit):
            safe_installer.install_packages(
                app_name="test_app",
                requirements_path="dummy_requirements.txt",
                python_executable="python"
            )

        os.remove("dummy_requirements.txt")

if __name__ == '__main__':
    unittest.main()
