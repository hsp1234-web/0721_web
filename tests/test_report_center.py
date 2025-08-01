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
    shutil.copytree(source_root, dest_root, ignore=shutil.ignore_patterns('.git', '__pycache__', '.venv', 'ALL_DATE'))
    return dest_root

def run_launch_and_create_db(project_path):
    """Helper function to run the main app to generate a state.db file."""
    db_file = project_path / "state.db"
    launch_script = project_path / "scripts" / "launch.py"
    config_file = project_path / "config.json"

    # Create a config for FAST_TEST_MODE
    config_data = {"FAST_TEST_MODE": True, "TIMEZONE": "Asia/Taipei"}
    config_file.write_text(json.dumps(config_data))

    command = [sys.executable, str(launch_script), "--db-file", str(db_file)]
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
    Tests the full E2E workflow of the new Report Center dashboard.
    """
    # --- Part 1: Generate real data ---
    run_launch_and_create_db(project_path)

    # --- Part 2: Run the Report Center in a thread ---
    # We need to load the `run/report.py` as a module to run its main()
    spec = importlib.util.spec_from_file_location("report_center", project_path / "run" / "report.py")
    report_center_module = importlib.util.module_from_spec(spec)

    # Mock PROJECT_FOLDER_NAME before executing the module
    report_center_module.PROJECT_FOLDER_NAME = project_path.name

    spec.loader.exec_module(report_center_module)

    # Run the main function in a thread so the test can interact with it
    report_server_thread = threading.Thread(target=report_center_module.main, daemon=True)
    report_server_thread.start()

    try:
        # --- Part 3: Wait for the Report Center to be ready ---
        max_wait = 120 # Can be long due to venv creation and pip install
        start_time = time.time()
        is_ready = False
        while time.time() - start_time < max_wait:
            try:
                with httpx.Client() as client:
                    response = client.get("http://localhost:8089/api/status", timeout=2)
                if response.status_code == 200 and response.json().get("status") == "準備就緒":
                    is_ready = True
                    break
            except httpx.ConnectError:
                time.sleep(2)

        if not is_ready:
            pytest.fail(f"Report Center API did not become ready within {max_wait} seconds.", pytrace=False)

        # --- Part 4: Request a report and verify content ---
        with httpx.Client() as client:
            response = client.post("http://localhost:8089/api/generate", json={"type": "summary"}, timeout=30)

        assert response.status_code == 200
        data = response.json()
        assert "reports" in data
        assert "summary" in data["reports"]
        assert "綜合戰情簡報" in data["reports"]["summary"]
        assert "平均 CPU 使用率" in data["reports"]["summary"]

    finally:
        # The report center runs an infinite loop, so we can't join the thread.
        # The test finishing will cause the daemon thread to exit.
        pass
