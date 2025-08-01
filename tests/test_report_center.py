import sys
import subprocess
import time
import json
import httpx
from pathlib import Path
import pytest
import shutil
import threading
import importlib
import re

# Mark all tests in this file as 'e2e' and 'slow'
pytestmark = [pytest.mark.e2e, pytest.mark.slow]

@pytest.fixture
def project_path(tmp_path):
    """
    Creates a temporary directory and copies the entire project into it.
    This provides a clean, isolated environment for each test run.
    """
    source_root = Path(__file__).parent.parent
    dest_root = tmp_path / "project"
    shutil.copytree(source_root, dest_root, ignore=shutil.ignore_patterns('.git', '__pycache__', '.venv', 'ALL_DATE', '.pytest_cache'))
    # Also create the /content directory for the symlink logic
    (tmp_path / "content").mkdir(exist_ok=True)
    return dest_root

def run_launch_and_create_db(project_path):
    """Helper function to run the main app to generate a state.db file."""
    db_file = project_path / "state.db"
    launch_script = project_path / "scripts" / "launch.py"
    config_file = project_path / "config.json"

    # Create a config for FAST_TEST_MODE
    config_data = {"FAST_TEST_MODE": True, "TIMEZONE": "Asia/Taipei", "INTERNAL_API_PORT": 8088}
    config_file.write_text(json.dumps(config_data))

    command = [sys.executable, str(launch_script), "--db-file", str(db_file), "--api-port", "8088"]
    process = subprocess.Popen(command, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    try:
        max_wait = 60
        start_time = time.time()
        is_ready = False
        while time.time() - start_time < max_wait:
            try:
                with httpx.Client() as client:
                    response = client.get("http://localhost:8088/api/v1/status", timeout=2)
                if response.status_code == 200:
                    is_ready = True
                    break
            except httpx.ConnectError:
                time.sleep(1)

        if not is_ready:
            pytest.fail(f"Main app API server did not become ready within {max_wait} seconds.", pytrace=False)

        with httpx.Client() as client:
            client.post("http://localhost:8088/api/v1/shutdown", timeout=10)
        process.communicate(timeout=30)
    finally:
        if process.poll() is None:
            process.kill()

    assert db_file.exists(), "state.db was not created by the main application."


def test_report_center_full_workflow(project_path):
    """
    Tests the full E2E workflow of the new Report Center dashboard,
    including dynamic port finding and the archive functionality.
    """
    # --- Part 1: Generate real data ---
    run_launch_and_create_db(project_path)

    # --- Part 2: Run the Report Center in a thread ---
    spec = importlib.util.spec_from_file_location("report_center", project_path / "run" / "report.py")
    report_center_module = importlib.util.module_from_spec(spec)

    # Mock user-configurable variables
    report_center_module.PROJECT_FOLDER_NAME = project_path.name
    report_center_module.REPORT_ARCHIVE_FOLDER = "test_archive"

    # We need to load the module's code before starting the thread
    spec.loader.exec_module(report_center_module)

    report_server_thread = threading.Thread(target=report_center_module.main, daemon=True)
    report_server_thread.start()

    api_port = None
    try:
        # --- Part 3: Wait for the Report Center to be ready and get its port ---
        max_wait = 180 # Increased timeout for CI environments
        start_time = time.time()
        is_ready = False
        while time.time() - start_time < max_wait:
            # The port is not known initially, so we can't query the API yet.
            # Instead, we check the shared_state which is manipulated by the thread.
            # This is a bit of a hack, but necessary for testing this architecture.
            if report_center_module.shared_state.get("status") == "準備就緒":
                 api_port = report_center_module.shared_state.get("api_port")
                 is_ready = True
                 break
            if report_center_module.shared_state.get("status") == "環境準備失敗":
                 pytest.fail(f"Report Center background worker failed: {report_center_module.shared_state.get('error')}")
            time.sleep(2)

        if not is_ready or not api_port:
            pytest.fail(f"Report Center API did not become ready within {max_wait} seconds.", pytrace=False)

        # --- Part 4: Test report generation API ---
        with httpx.Client() as client:
            response = client.post(f"http://localhost:{api_port}/api/generate", json={"type": "summary"}, timeout=30)

        assert response.status_code == 200
        data = response.json()
        assert "reports" in data and "summary" in data["reports"]
        assert "綜合戰情簡報" in data["reports"]["summary"]

        # --- Part 5: Test archiving API ---
        with httpx.Client() as client:
            response = client.post(f"http://localhost:{api_port}/api/archive", timeout=30)

        assert response.status_code == 200
        archive_data = response.json()
        assert "path" in archive_data

        # --- Part 6: Verify archived files ---
        archive_path = Path(archive_data["path"])
        assert archive_path.is_dir()

        expected_files = ["任務總結報告.md", "效能分析報告.md", "詳細日誌報告.md"]
        found_files = [f.name for f in archive_path.iterdir()]
        for f in expected_files:
            assert f in found_files, f"Expected archived file '{f}' not found."

    finally:
        # The main loop in report.py is infinite, so we can't join the thread.
        # It's a daemon, so it will be terminated when the test process exits.
        # We can try to shutdown the server gracefully for good measure.
        if api_port:
            try:
                # This may or may not work depending on timing, but it's good practice.
                httpx.post(f"http://localhost:{api_port}/shutdown_gracefully_for_test", timeout=2)
            except (httpx.ConnectError, httpx.ReadTimeout):
                pass

        report_server_thread.join(timeout=1) # Give it a moment to shutdown
