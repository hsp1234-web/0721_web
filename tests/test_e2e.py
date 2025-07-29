# -*- coding: utf-8 -*-
"""
端到端 (E2E) 測試，用於驗證整個應用的啟動、關閉、日誌記錄和 TUI 顯示等功能。
"""
import os
import sys
import time
import subprocess
from pathlib import Path
import pytest
from contextlib import contextmanager

# --- 專案根目錄 ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

@contextmanager
def run_server(command: list[str], timeout: int = 10):
    """
    一個上下文管理器，用於在背景啟動一個伺服器進程，
    並在測試結束後將其關閉。
    """
    process = None
    try:
        # 在背景啟動伺服器
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        # 等待一段時間，讓伺服器有足夠的時間啟動
        time.sleep(timeout)
        yield process
    finally:
        if process:
            process.terminate()
            process.wait()

def test_launch_py_no_proxy():
    """
    測試 `launch.py --no-proxy` 是否能正常啟動和關閉。
    """
    command = ["python", str(PROJECT_ROOT / "launch.py"), "--no-proxy"]
    with run_server(command) as process:
        # 檢查伺服器是否仍在運行
        assert process.poll() is None, "伺服器在測試期間意外退出"

        # 檢查日誌輸出
        output = process.stdout.read()
        assert "所有 App 已在背景啟動。" in output
        assert "逆向代理未啟動" in output

def test_phoenix_starter_non_interactive():
    """
    測試 `phoenix_starter.py --non-interactive` 是否能正常運行並自動退出。
    """
    command = ["python", str(PROJECT_ROOT / "phoenix_starter.py"), "--non-interactive"]
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        encoding='utf-8',
        errors='replace',
        timeout=120 # 給予足夠的時間來安裝依賴和運行測試
    )

    # 檢查返回碼
    assert result.returncode == 0, f"phoenix_starter.py 執行失敗: {result.stderr}"

    # 檢查日誌輸出
    assert "所有任務已完成" in result.stdout
    assert "請按 Enter 鍵退出..." not in result.stdout

def test_log_files_creation():
    """
    測試日誌檔案是否被正確建立。
    """
    log_dir = PROJECT_ROOT / "logs"
    # 執行 `phoenix_starter.py` 以生成日誌檔案
    command = ["python", str(PROJECT_ROOT / "phoenix_starter.py"), "--non-interactive"]
    subprocess.run(command, timeout=120)

    # 檢查日誌目錄是否存在
    assert log_dir.is_dir(), "日誌目錄未被建立"

    # 檢查是否有為 quant 和 transcriber App 建立的日誌檔案
    quant_logs = list(log_dir.glob("install_quant_*.log"))
    transcriber_logs = list(log_dir.glob("install_transcriber_*.log"))

    assert len(quant_logs) > 0, "找不到 quant App 的日誌檔案"
    assert len(transcriber_logs) > 0, "找不到 transcriber App 的日誌檔案"

    # 檢查日誌檔案的內容
    with open(quant_logs[0], 'r', encoding='utf-8') as f:
        content = f.read()
        assert "--- 開始為 App 'quant' 進行安全安裝 ---" in content
        assert "--- App 'quant' 所有套件均已成功安裝 ---" in content
