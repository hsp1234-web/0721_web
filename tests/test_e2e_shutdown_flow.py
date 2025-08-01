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


def test_report_generator_script_with_auto_install(project_path):
    """
    Tests the `run/report.py` script to ensure its auto-dependency-installation
    feature works correctly.
    """
    # 1. Setup the environment
    # We use the real scripts, not mocks.
    # A dummy state.db and config.json are needed for the script to run.
    db_file = project_path / "state.db"
    db_file.touch()
    config_file = project_path / "config.json"
    config_file.write_text(json.dumps({"TIMEZONE": "Asia/Taipei"}))

    # Ensure the report requirements file exists
    assert (project_path / "scripts" / "requirements-report.txt").exists()

    # 2. Get the content of our `run/report.py` wrapper
    report_runner_script_path = project_path / "run" / "report.py"
    assert report_runner_script_path.exists()
    report_runner_script_content = report_runner_script_path.read_text(encoding='utf-8')

    # Extract the Python code from the Colab cell
    code_lines = []
    in_code_section = False
    for line in report_runner_script_content.splitlines():
        if "#@markdown >" in line and "點擊「執行」以生成報告" in line:
            in_code_section = True
            continue
        if in_code_section:
            code_lines.append(line)
    python_code_to_run = "\n".join(code_lines)
    assert "uv pip install" in python_code_to_run

    # 3. Simulate the Colab environment and execute the code
    exec_globals = {
        "PROJECT_FOLDER_NAME": project_path.name,
        "GENERATE_SUMMARY_REPORT": False, # Don't need to see output
        "GENERATE_PERFORMANCE_REPORT": False,
        "GENERATE_DETAILED_LOG_REPORT": False,
        "display": lambda *args, **kwargs: None,
        "Code": lambda data, language: None,
        "Markdown": lambda data: None,
    }

    content_dir = Path("/content")
    content_dir.mkdir(exist_ok=True)
    symlink_path = content_dir / project_path.name
    if not symlink_path.exists():
        symlink_path.symlink_to(project_path)

    try:
        # The key assertion: executing this code should not raise any exceptions,
        # especially not a ModuleNotFoundError. This proves the auto-install
        # and path resolution logic is working.
        exec(python_code_to_run, exec_globals)

    except Exception as e:
        pytest.fail(f"Execution of the report runner script failed: {e}")

    finally:
        if symlink_path.is_symlink():
            symlink_path.unlink()
