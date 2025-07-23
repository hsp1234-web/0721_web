import pytest

def test_import_all_modules():
    """
    Imports all modules in the src directory to check for import errors.
    """
    try:
            from integrated_platform.src import archiver
            from integrated_platform.src import config
            from integrated_platform.src import generate_log_report
            from integrated_platform.src import integrated_logic
            from integrated_platform.src import main
            from integrated_platform.src import sqlite_log_handler
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")
