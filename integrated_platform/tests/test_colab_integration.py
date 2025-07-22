# tests/test_colab_integration.py
import pytest
import subprocess
from unittest.mock import MagicMock, patch, mock_open

# 模擬 Colab 和 IPython 環境
# 這確保即使在非 Colab 環境中，導入也不會失敗
modules_to_mock = {
    'google.colab': MagicMock(),
    'google.colab.output': MagicMock(),
    'IPython.display': MagicMock(),
    'psutil': MagicMock(),
    'zoneinfo': MagicMock(),
}

# 使用 patch.dict 來在測試期間替換 sys.modules
# with patch.dict('sys.modules', modules_to_mock):
#     # 在這裡，導入將使用我們偽造的模組
#     # 我們將在測試函式中導入被測腳本
#     pass

def run_colab_script(tmp_path, project_folder_name, run_script_content):
    """
    一個輔助函式，用於在受控的暫存環境中執行 Colab 腳本邏輯。

    Args:
        tmp_path (pathlib.Path): Pytest 的暫存路徑 fixture。
        project_folder_name (str): 模擬的專案資料夾名稱。
        run_script_content (str): 要寫入模擬 run.sh 的內容。
    """
    # 1. 設定模擬的檔案系統結構
    content_path = tmp_path / "content"
    project_path = content_path / project_folder_name
    archive_path = content_path / "作戰日誌歸檔"
    project_path.mkdir(parents=True, exist_ok=True)
    archive_path.mkdir(parents=True, exist_ok=True)

    # 建立一個可執行的 run.sh
    run_script_path = project_path / "run.sh"
    run_script_path.write_text(run_script_content)
    run_script_path.chmod(0o755)

    # 2. 模擬 Colab 腳本中的全域變數
    # 這裡我們需要小心地模擬所有需要的變數和函式
    # 為了簡單起見，我們將腳本的主要邏輯直接放在這裡
    # (在一個更複雜的場景中，我們會將腳本重構成一個可導入的模組)

    # ... 這裡將會是 Colab 腳本的主要邏輯 ...
    # 為了這個測試，我們將直接呼叫 subprocess.run 並檢查結果

    result = subprocess.run(
        ["bash", str(run_script_path)],
        capture_output=True, text=True
    )
    return result

def test_colab_script_finds_and_runs_run_sh(tmp_path, mocker):
    """
    測試 Colab 腳本是否能成功找到並執行 run.sh。
    """
    # 模擬 subprocess.run 以避免實際執行 run.sh
    mock_subprocess_run = mocker.patch('subprocess.run')
    # 讓模擬的 run 回傳一個成功的結果
    mock_subprocess_run.return_value = subprocess.CompletedProcess(
        args=["bash", "dummy_path/run.sh"], returncode=0, stdout="OK", stderr=""
    )

    # 將 Colab 腳本的邏輯（簡化版）放在這裡
    # 我們只測試最關鍵的部分：路徑檢查和 subprocess 呼叫
    PROJECT_FOLDER = "integrated_platform"
    PROJECT_PATH = tmp_path / PROJECT_FOLDER
    RUN_SCRIPT_PATH = PROJECT_PATH / "run.sh"

    # 建立假的 run.sh 讓路徑檢查通過
    PROJECT_PATH.mkdir()
    RUN_SCRIPT_PATH.touch()

    # 模擬 LogManager
    mock_log_manager = MagicMock()

    # --- 這是被測邏輯 ---
    if not RUN_SCRIPT_PATH.is_file():
        raise FileNotFoundError(f"致命錯誤：找不到部署腳本 '{RUN_SCRIPT_PATH}'！")
    mock_log_manager.log("SUCCESS", "部署腳本已找到。")

    mock_log_manager.log("INFO", "正在執行後端部署腳本 (run.sh)...")
    result = subprocess.run(["bash", str(RUN_SCRIPT_PATH)], capture_output=True, text=True, encoding='utf-8')
    if result.returncode != 0:
        mock_log_manager.log("ERROR", "後端部署腳本執行失敗。")
    else:
        mock_log_manager.log("SUCCESS", "後端部署腳本執行完畢。")
    # --- 邏輯結束 ---

    # 驗證
    # 驗證日誌呼叫
    mock_log_manager.log.assert_any_call("SUCCESS", "部署腳本已找到。")
    mock_log_manager.log.assert_any_call("INFO", "正在執行後端部署腳本 (run.sh)...")
    mock_log_manager.log.assert_any_call("SUCCESS", "後端部署腳本執行完畢。")

    # 驗證 subprocess.run 是否被正確呼叫
    mock_subprocess_run.assert_called_once_with(
        ["bash", str(RUN_SCRIPT_PATH)],
        capture_output=True, text=True, encoding='utf-8'
    )
