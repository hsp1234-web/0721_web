# -*- coding: utf-8 -*-
import subprocess
import sys
import pytest
import shutil
from pathlib import Path
from unittest.mock import patch

# 由於我們要測試的模組在 core_utils 中，我們需要確保它可以被導入
# pytest 在執行時會自動處理路徑，但為了清晰起見，我們保留這個
sys.path.insert(0, str(Path(__file__).parent.parent))
from core_utils import safe_installer

import collections

@pytest.mark.slow
@patch('shutil.disk_usage')
def test_installation_stops_on_low_disk_space(mock_disk_usage):
    """
    驗證當 shutil.disk_usage 回報磁碟空間不足時，安裝流程是否會被中止。
    這是一個精確的單元測試，直接測試 safe_installer 的核心邏輯。
    """
    # 模擬磁碟空間不足的情況
    # shutil.disk_usage 返回一個 namedtuple，我們需要精確模擬這個行為
    Usage = collections.namedtuple("Usage", ["total", "used", "free"])
    mock_disk_usage.return_value = Usage(total=1024**3, used=1024**3, free=100 * 1024**2) # 100MB free

    # 建立一個假的 app 和 requirements
    app_name = "test_app_fail"
    req_path = Path("temp_reqs_for_fail_test.txt")
    req_path.write_text("some-package\n")

    # 這個 python 執行檔路徑在此測試中不重要，因為我們期望在執行前就失敗
    python_executable = sys.executable

    # 使用 pytest.raises 來斷言 SystemExit 是否被引發
    with pytest.raises(SystemExit) as excinfo:
        safe_installer.install_packages(app_name, str(req_path), python_executable)

    # 斷言 SystemExit 的退出訊息是否包含預期的錯誤
    assert "資源不足" in str(excinfo.value)

    # 清理臨時檔案
    req_path.unlink()

@pytest.mark.e2e
@pytest.mark.very_slow
@pytest.mark.skip(reason="此測試會安裝所有應用的完整依賴，執行時間過長，不適合在 CI/CD 環境中頻繁運行")
def test_full_run_with_normal_resources(full_mode_config):
    """
    執行一個完整的 `launch.py` 流程，以驗證在正常資源下，
    所有應用都能被正確安裝和啟動，並產生 Colab URL。
    """
    # 清理舊的 venv 和日誌
    for app_dir in ["apps/main_dashboard", "apps/quant", "apps/transcriber"]:
        venv_path = Path(app_dir) / ".venv"
        if venv_path.exists():
            shutil.rmtree(venv_path, ignore_errors=True)
    db_file = Path("logs/e2e_full_run.db")
    if db_file.exists():
        db_file.unlink()

    try:
        # 執行 launch.py。它會使用 conftest.py 中的 full_mode_config
        result = subprocess.run(
        [sys.executable, "scripts/launch.py", "--db-file", str(db_file)],
            capture_output=True,
            text=True,
            timeout=1800, # 30 分鐘超時
            encoding='utf-8',
            check=True
        )

        output = result.stdout + result.stderr

        # 斷言：我們尋找一個更可靠的成功標誌，即 Colab URL 已生成
        # 這表示主儀表板已成功啟動，並且後續流程也已觸發
        assert "主儀表板 Colab 代理 URL" in output, "在日誌中未找到 '主儀表板 Colab 代理 URL' 的成功訊息"

    except subprocess.TimeoutExpired as e:
        pytest.fail(f"完整運行測試因超時而失敗。\n輸出:\n{e.stdout}\n錯誤:\n{e.stderr}")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"完整運行測試失敗，返回碼: {e.returncode}。\n輸出:\n{e.stdout}\n錯誤:\n{e.stderr}")
