# -*- coding: utf-8 -*-
import subprocess
import sys
import pytest
from unittest.mock import patch
import shutil

# 測試資源保護機制的專用測試案例

@pytest.mark.slow
@patch('core_utils.resource_monitor.is_resource_sufficient')
def test_installation_stops_on_low_disk_space(mock_is_resource_sufficient):
    """
    驗證當 is_resource_sufficient 回報資源不足時，安裝流程是否會被中止。
    這是一個對 `safe_installer` 邏輯的單元測試，比執行完整 `launch.py` 更快、更隔離。
    """
    # 模擬資源不足的情況
    mock_is_resource_sufficient.return_value = (False, "模擬的磁碟空間不足")

    # 我們需要一個假的 requirements.txt 和一個假的 python 可執行檔路徑
    # 這個測試的重點是檢查 SystemExit 是否被引發，而不是實際的安裝
    app_name = "test_app_fail"
    req_content = "some-package\n"
    req_path = "temp_reqs.txt"
    with open(req_path, "w") as f:
        f.write(req_content)

    python_executable = sys.executable # 在此測試中，這個路徑是什麼無所謂

    command = [
        sys.executable,
        "-m", "core_utils.safe_installer",
        app_name,
        req_path,
        python_executable
    ]

    # 執行安裝腳本，並期望它因為 SystemExit 而失敗
    process = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding='utf-8'
    )

    # 斷言 1: 程序應該以非零的狀態碼退出
    assert process.returncode != 0, "程序應該因資源不足而失敗，但它成功了"

    # 斷言 2: stderr 應該包含我們預期的錯誤訊息
    expected_error_message = "因資源不足，安裝程序已在安裝 'some-package' 前中止。"
    assert expected_error_message in process.stderr, f"預期的錯誤訊息 '{expected_error_message}' 不在 stderr 中"

@pytest.mark.e2e
@pytest.mark.very_slow
def test_full_run_with_normal_resources():
    """
    執行一個完整的 `launch.py --full` 流程，以驗證在正常資源下，
    所有應用都能被正確安裝和啟動。
    這個測試同時也作為收集安裝耗時數據的基礎。
    """
    # 為了確保測試環境乾淨，刪除可能存在的舊日誌和 venv
    for app_dir in ["apps/main_dashboard", "apps/quant", "apps/transcriber"]:
        venv_path = f"{app_dir}/.venv"
        if shutil.which(venv_path):
            shutil.rmtree(venv_path, ignore_errors=True)

    # 執行 launch.py --full。我們設定一個較短的超時，因為我們只關心安裝和啟動，
    # 而不是長時間的待命。
    try:
        # 使用 subprocess.run 來執行，並設定 timeout
        # 注意: 這個測試會很慢，因為它要下載和安裝很多套件
        result = subprocess.run(
            [sys.executable, "launch.py", "--full"],
            capture_output=True,
            text=True,
            timeout=1800, # 給予 30 分鐘的超時時間
            encoding='utf-8',
            check=True # 如果返回非零狀態碼，會拋出 CalledProcessError
        )

        # 檢查日誌中是否有成功啟動所有服務的訊息
        assert "所有核心服務已成功啟動" in result.stdout or "所有服務運行中" in result.stdout
        assert "主儀表板 Colab 代理 URL" in result.stdout

    except subprocess.TimeoutExpired as e:
        pytest.fail(f"完整運行測試因超時而失敗 (超過 1800 秒)。\n輸出:\n{e.stdout}\n錯誤:\n{e.stderr}")
    except subprocess.CalledProcessError as e:
        pytest.fail(f"完整運行測試失敗，返回碼: {e.returncode}。\n輸出:\n{e.stdout}\n錯誤:\n{e.stderr}")
