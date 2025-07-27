import subprocess
import sys
from pathlib import Path
import toml
import pytest

# 將 launcher 目錄添加到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

@pytest.mark.e2e
def test_launcher_end_to_end():
    """
    一個端到端的測試，模擬 Colab 筆記本的行為。
    """
    # 建立一個模擬的 /content 目錄
    content_dir = Path("/tmp/mock_content")
    content_dir.mkdir(exist_ok=True)

    # 模擬 Colab 表單輸入，建立設定檔
    config_dir = Path(__file__).parent.parent / "config"
    config_dir.mkdir(exist_ok=True)
    settings_path = config_dir / "settings.toml"

    settings = {
        'project': {
            'repository_url': "https://github.com/hsp1234-web/0721_web",
            'target_branch_or_tag': "2.1.2",
            'project_folder_name': "WEB1_E2E_TEST",
            'force_repo_refresh': True
        },
        'launcher': {
            'refresh_rate_seconds': 0.1,
            'log_display_lines': 10,
            'timezone': 'Asia/Taipei'
        },
        'log_archive': {'enabled': False},
        'mode': {'test_mode': True}
    }
    with open(settings_path, 'w') as f:
        toml.dump(settings, f)

    # 執行啟動器主腳本
    launcher_main_script = Path(__file__).parent.parent / "src/main.py"

    try:
        # 執行主腳本並設定超時
        process = subprocess.run(
            [sys.executable, str(launcher_main_script)],
            capture_output=True,
            text=True,
            timeout=120  # 2分鐘超時
        )

        # 檢查返回碼是否為 0，表示成功退出
        assert process.returncode == 0, f"測試失敗，返回碼非零。Stderr: {process.stderr}"

        # 檢查 stderr 是否有我們不希望看到的錯誤訊息
        assert "發生未預期的錯誤" not in process.stderr
        assert "ModuleNotFoundError" not in process.stderr
        assert "PermissionError" not in process.stderr

        # 由於 rich 的 Live 輸出機制，直接檢查 stdout 很不穩定。
        # 程式能成功退出本身就是一個很強的成功信號。

    except subprocess.TimeoutExpired:
        pytest.fail("啟動器端到端測試超時。")
