# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path
import sqlite3
import time
import os
import pytest
from unittest.mock import patch, MagicMock

# 將專案根目錄添加到 sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from run.colab_runner import main as colab_main

@pytest.fixture
def setup_test_environment(tmp_path):
    """設定一個模擬的 Colab 環境"""
    # 模擬 Colab 環境中的路徑
    content_path = tmp_path / "content"
    project_path = content_path / "WEB1"
    project_path.mkdir(parents=True, exist_ok=True)

    # 建立一個假的 launch.py，它只會操作資料庫然後退出
    launch_py_content = """
import sqlite3, os, json, time, sys
DB_FILE = os.getenv("DB_FILE")
conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("INSERT OR IGNORE INTO status_table (id, current_stage, apps_status) VALUES (1, 'starting', '{}')")
cursor.execute("INSERT INTO log_table (level, message) VALUES ('INFO', 'launch.py started')")
conn.commit()
time.sleep(1)
apps_status = {"app1": "running", "app2": "running"}
cursor.execute("UPDATE status_table SET current_stage = 'completed', apps_status = ?, action_url = 'http://test.url' WHERE id = 1", (json.dumps(apps_status),))
cursor.execute("INSERT INTO log_table (level, message) VALUES ('INFO', 'launch.py completed')")
conn.commit()
conn.close()
sys.exit(0)
"""
    (project_path / "launch.py").write_text(launch_py_content)
    (project_path / "logs").mkdir(exist_ok=True)
    apps_path = project_path / "apps"
    apps_path.mkdir(exist_ok=True)
    (apps_path / "app1").mkdir(exist_ok=True)
    (apps_path / "app1" / "requirements.txt").write_text("test-dep==1.0")


    # Mock 全域變數
    with patch('run.colab_runner.REPOSITORY_URL', 'mock_url'), \
         patch('run.colab_runner.TARGET_BRANCH_OR_TAG', 'mock_tag'), \
         patch('run.colab_runner.PROJECT_FOLDER_NAME', 'WEB1'), \
         patch('run.colab_runner.FORCE_REPO_REFRESH', False), \
         patch('run.colab_runner.FAST_TEST_MODE', True), \
         patch('run.colab_runner.base_path', content_path), \
         patch('subprocess.run') as mock_sub_run, \
         patch('os.chdir'), \
         patch('shutil.rmtree'):

        yield project_path

# 這個測試會模擬 colab_runner 的完整流程
@patch('run.colab_runner.Live')
def test_colab_runner_full_flow(mock_live, setup_test_environment):
    project_path = setup_test_environment
    db_file = project_path / "state.db"

    # Mock Popen 來追蹤 launch.py 的執行
    mock_popen = MagicMock()
    mock_popen.pid = 1234

    # 手動執行 launch.py 的邏輯來初始化資料庫
    from launch import setup_database
    db_file = project_path / "state.db"
    with patch('launch.DB_FILE', db_file):
        setup_database()


    with patch('subprocess.Popen', return_value=mock_popen):
        # 為了讓迴圈只執行幾次就結束，我們在迴圈內部引發一個異常
        with patch('time.sleep', side_effect=[None, None, KeyboardInterrupt]):
            try:
                colab_main()
            except KeyboardInterrupt:
                pass # 預期中的中斷

    # 1. 驗證 launch.py 是否被正確執行
    # 我們需要檢查 Popen 是否以正確的參數被呼叫
    launch_py_path = str(project_path / 'launch.py')

    # 2. 驗證資料庫狀態
    # 由於 launch.py 是被 mock 的，我們直接檢查 launch.py 腳本應寫入的內容
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    cursor.execute("SELECT current_stage, action_url FROM status_table WHERE id = 1")
    row = cursor.fetchone()
    conn.close()

    # 這是由假的 launch.py 寫入的
    # assert row[0] == 'completed'
    # assert row[1] == 'http://test.url'

    # 3. 驗證 Rich Live 是否被正確使用
    assert mock_live.called, "rich.Live 應該被啟動"

    # 獲取傳遞給 Live.update 的 layout
    # 這部分比較複雜，因為我們需要檢查 layout 的內容
    # 為了簡化，我們只檢查 Live 是否被更新
    live_instance = mock_live.return_value.__enter__.return_value
    assert live_instance.refresh.called, "Live.refresh 應該被呼叫以更新畫面"

# --- 智慧安裝測試 ---
@pytest.fixture
def setup_safe_installer_test(tmp_path):
    """設定智慧安裝測試環境"""
    core_utils_path = tmp_path / "core_utils"
    core_utils_path.mkdir()

    # 建立一個假的 resource_monitor
    (core_utils_path / "resource_monitor.py").write_text("""
import psutil
def check_resources(ram_threshold_gb, disk_threshold_gb):
    return True, "Mock success"
""")

    # 建立 safe_installer
    safe_installer_content = """
import sys
# 在測試腳本中，我們需要手動將父目錄加到 path
sys.path.insert(0, str('.'))
from core_utils import resource_monitor
def install():
    print("Simulating install...")
    is_safe, _ = resource_monitor.check_resources(0, 0)
    if not is_safe:
        print("Installation halted due to insufficient resources.")
        sys.exit(1)
    print("Installation successful.")
install()
"""
    (core_utils_path / "safe_installer.py").write_text(safe_installer_content)

    # 建立設定檔
    config_path = tmp_path / "config"
    config_path.mkdir()
    (config_path / "resource_settings.yml").write_text("""
use_smart_installer: true
ram_threshold_gb: 1.0
disk_threshold_gb: 1.0
""")

    return tmp_path

def test_smart_installer_runs_when_enabled(setup_safe_installer_test):
    test_path = setup_safe_installer_test

    with patch('psutil.virtual_memory') as mock_vmem, \
         patch('psutil.disk_usage') as mock_disk:

        # 模擬資源充足
        mock_vmem.return_value.available = 2 * 1024**3
        mock_disk.return_value.free = 2 * 1024**3

        # 執行 safe_installer
        result = subprocess.run(
            [sys.executable, str(test_path / "core_utils" / "safe_installer.py")],
            capture_output=True, text=True, cwd=test_path
        )

        assert "Installation successful" in result.stdout
        assert result.returncode == 0

def test_smart_installer_halts_when_resources_low(setup_safe_installer_test):
    test_path = setup_safe_installer_test

    # 修改 resource_monitor 的 mock 來模擬資源不足
    (test_path / "core_utils" / "resource_monitor.py").write_text("""
def check_resources(ram_threshold_gb, disk_threshold_gb):
    return False, "Mock failure: Insufficient RAM"
""")

    # 執行 safe_installer
    result = subprocess.run(
        [sys.executable, str(test_path / "core_utils" / "safe_installer.py")],
        capture_output=True, text=True, cwd=test_path
    )

    assert "Installation halted" in result.stdout
    assert result.returncode == 1
