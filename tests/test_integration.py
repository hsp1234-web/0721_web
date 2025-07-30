# -*- coding: utf-8 -*-
import unittest
import subprocess
import sys
import os
import time
from pathlib import Path
from unittest.mock import patch

import httpx

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core_utils import safe_installer

class TestIntegration(unittest.TestCase):

    def setUp(self):
        self.test_project_path = PROJECT_ROOT / "test_integration_project"
        if self.test_project_path.exists():
            subprocess.run(['rm', '-rf', str(self.test_project_path)])
        self.test_project_path.mkdir()

        # 建立一個假的 apps 目錄結構
        self.apps_path = self.test_project_path / "apps"
        self.apps_path.mkdir()
        (self.apps_path / "app1").mkdir()
        with open(self.apps_path / "app1" / "requirements.txt", "w") as f:
            f.write("requests\n")

    def tearDown(self):
        if self.test_project_path.exists():
            subprocess.run(['rm', '-rf', str(self.test_project_path)])

    def test_full_flow(self):
        # 1. 準備環境
        env = os.environ.copy()
        env["DB_FILE"] = str(self.test_project_path / "state.db")
        env["API_PORT"] = "8082" # 使用不同的埠，避免與其他測試衝突
        env["PYTHONPATH"] = str(PROJECT_ROOT)

        # 2. 啟動後端服務
        run_log = self.test_project_path / "run.log"

        with open(run_log, "w") as f_run:
            run_process = subprocess.Popen(
                [sys.executable, str(PROJECT_ROOT / "run.py")],
                env=env, stdout=f_run, stderr=subprocess.STDOUT, cwd=self.test_project_path
            )

            # 3. 健康檢查
            self.assertTrue(self._wait_for_service(8082), "後端服務在指定時間內未啟動")

            # 4. 驗證 API
            response = httpx.get("http://localhost:8082/api/status")
            self.assertEqual(response.status_code, 200)
            status_data = response.json()
            self.assertIn("current_stage", status_data)

            # 5. 驗證 safe_installer
            with patch('core_utils.safe_installer.is_resource_sufficient') as mock_is_resource_sufficient:
                # 模擬資源充足
                mock_is_resource_sufficient.return_value = (True, "OK")

                # 建立一個假的 python venv
                venv_path = self.test_project_path / ".venv"
                subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
                python_executable = str(venv_path / "bin" / "python")

                with patch('subprocess.run') as mock_subprocess_run:
                    result = safe_installer.install_packages(
                        app_name="app1",
                        requirements_path=str(self.apps_path / "app1" / "requirements.txt"),
                        python_executable=python_executable
                    )
                    self.assertEqual(result, 0)
                    mock_subprocess_run.assert_called()

                # 模擬資源不足
                mock_is_resource_sufficient.return_value = (False, "FAIL")
                result = safe_installer.install_packages(
                    app_name="app1",
                    requirements_path=str(self.apps_path / "app1" / "requirements.txt"),
                    python_executable=python_executable
                )
                self.assertEqual(result, 1)

            # 6. 清理
            run_process.terminate()
            run_process.wait()

    def _wait_for_service(self, port, timeout=60):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = httpx.get(f"http://localhost:{port}/api/health")
                if response.status_code == 200:
                    return True
            except httpx.ConnectError:
                pass
            time.sleep(1)
        return False

if __name__ == '__main__':
    unittest.main()
