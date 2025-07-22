import pytest

def test_import_all_modules():
    """
    Imports all modules in the src directory to check for import errors.
    """
    try:
        from src import archiver  # noqa: F401
        from src import commander_console  # noqa: F401
        from src import display_manager  # noqa: F401
        from src import generate_log_report  # noqa: F401
        from src import log_manager  # noqa: F401
        from src import main  # noqa: F401
    except ImportError as e:
        pytest.fail(f"Failed to import modules: {e}")
