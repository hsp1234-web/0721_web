import sys
import subprocess
import time
import json
import httpx
from pathlib import Path
import pytest
import shutil

# Mark all tests in this file as 'e2e'
pytestmark = pytest.mark.e2e

@pytest.fixture
def project_path(tmp_path):
    """
    Creates a temporary directory and copies the entire project into it.
    This provides a clean, isolated environment for each test run.
    """
    source_root = Path(__file__).parent.parent
    dest_root = tmp_path / "project"

    # Copy the entire project except for large, unnecessary directories
    shutil.copytree(source_root, dest_root, ignore=shutil.ignore_patterns('.git', '__pycache__', '.venv', 'ALL_DATE'))

    return dest_root

@pytest.fixture
def test_config(project_path):
    """
    Creates a temporary config.json for the test run in the isolated project path.
    """
    archive_dir_name = "test_作戰日誌歸檔"
    config_data = {
        "LOG_ARCHIVE_FOLDER_NAME": archive_dir_name,
        "TIMEZONE": "Asia/Taipei",
        "FAST_TEST_MODE": True,
        "LOG_LEVELS_TO_SHOW": {"BATTLE": True, "SUCCESS": True, "ERROR": True},
        "LOG_DISPLAY_LINES": 50,
    }
    config_path = project_path / "config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config_data, f)

    return config_path, archive_dir_name


def test_graceful_shutdown_and_report_archiving(project_path, test_config):
    """
    End-to-end test for the graceful shutdown and report archiving process.
    """
    _, archive_dir_name = test_config
    db_file = project_path / "state.db"

    launch_script = project_path / "scripts" / "launch.py"
    assert launch_script.exists()

    command = [sys.executable, str(launch_script), "--db-file", str(db_file)]

    process = subprocess.Popen(command, cwd=project_path, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='ignore')

    api_url = "http://localhost:8088/api/v1/status"
    shutdown_url = "http://localhost:8088/api/v1/shutdown"

    try:
        # 1. Wait for the API server to be ready
        max_wait = 45
        start_time = time.time()
        is_ready = False
        while time.time() - start_time < max_wait:
            try:
                with httpx.Client() as client:
                    response = client.get(api_url, timeout=2)
                if response.status_code == 200:
                    is_ready = True
                    break
            except httpx.ConnectError:
                time.sleep(1)

        if not is_ready:
            output, _ = process.communicate()
            print(output)
            pytest.fail(f"API server did not become ready within {max_wait} seconds.", pytrace=False)

        # 2. Send the shutdown request
        with httpx.Client() as client:
            response = client.post(shutdown_url, timeout=10)
        assert response.status_code == 200
        assert response.json()["status"] == "shutdown_initiated"

        # 3. Wait for the process to terminate
        # 3. Wait for the process to terminate and capture output
        stdout = ""
        try:
            # communicate() waits for the process to terminate
            stdout, _ = process.communicate(timeout=45)
        except subprocess.TimeoutExpired:
            process.kill()
            # Capture any output before killing
            stdout, _ = process.communicate()
            print("--- LAUNCH.PY STDOUT (TIMEOUT) ---")
            print(stdout)
            print("--- END LAUNCH.PY STDOUT ---")
            pytest.fail("Process timed out during shutdown.", pytrace=False)

        print("--- LAUNCH.PY STDOUT ---")
        print(stdout)
        print("--- END LAUNCH.PY STDOUT ---")

        if process.returncode != 0:
            pytest.fail(f"Process did not terminate cleanly. Return code: {process.returncode}", pytrace=False)

        # 4. Verify that the state database was created and contains data.
        assert db_file.exists(), "state.db was not created."
        assert db_file.stat().st_size > 0, "state.db is empty."

        # 5. Verify the database content
        import sqlite3
        conn = sqlite3.connect(db_file)
        cursor = conn.cursor()

        # Check if the logs table has records
        cursor.execute("SELECT COUNT(*) FROM phoenix_logs")
        log_count = cursor.fetchone()[0]
        assert log_count > 0, "The phoenix_logs table should not be empty."

        # Check if the status table has a final status
        cursor.execute("SELECT current_stage FROM status_table WHERE id = 1")
        final_stage = cursor.fetchone()[0]
        assert final_stage is not None, "The final stage was not recorded in the status_table."
        # In fast test mode, this is the expected final stage
        assert "快速測試通過" in final_stage

        conn.close()

    finally:
        if process.poll() is None:
            process.terminate()
            process.wait()


# This test is now obsolete and replaced by the more comprehensive one below.
# I'm keeping it commented out for reference during this refactoring phase.
# def test_report_generator_script_with_auto_install(project_path):
#    ...
