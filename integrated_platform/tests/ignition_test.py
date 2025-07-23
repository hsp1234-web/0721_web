import pytest

def test_import_all_modules():
    """
    Imports all modules in the src directory to check for import errors.
    """
    try:
            from integrated_platform.src import archiver  # noqa: F401
            from integrated_platform.src import commander_console  # noqa: F401
            from integrated_platform.src.ui import display_manager  # noqa: F401
            from integrated_platform.src import generate_log_report  # noqa: F401
            from integrated_platform.src import log_manager  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")
