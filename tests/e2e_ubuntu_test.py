# -*- coding: utf-8 -*-
"""
e2e_ubuntu_test.py: 端對端 Ubuntu 測試儀

本腳本專為在標準 Linux 環境 (如 Ubuntu) 中對鳳凰之心專案進行完整的端對端測試而設計。
它不依賴任何 Google Colab 的特定功能，確保了核心應用程式生命週期的可測試性。

測試流程:
1.  在背景以子程序形式，完整啟動 `run/colab_runner.py`。
2.  監控其輸出，確認後端服務 (`launch.py`, `api_server.py`) 已啟動。
3.  主動向 `api_server.py` 的 `/api/health` 端點發送請求，驗證其健康狀況。
4.  接著，請求 `/api/status` 和 `/api/logs`，驗證數據 API 的功能性。
5.  模擬使用者操作，向 `colab_runner.py` 進程發送 `SIGINT` (Ctrl+C) 來觸發正常關閉流程。
6.  檢查 `reports/` 目錄，斷言三份必要的 Markdown 報告都已成功生成。
7.  確保所有子程序都已乾淨地退出。
"""

import subprocess
import time
import os
import signal
from pathlib import Path
import json
import requests

# --- 測試設定 ---
PROJECT_ROOT = Path(__file__).parent.resolve()
REPORTS_DIR = PROJECT_ROOT / "reports"
API_BASE_URL = "http://localhost:8080"

def print_header(msg):
    print(f"\n{'='*20} {msg} {'='*20}")

def cleanup():
    """清理舊的報告和日誌"""
    print_header("清理環境")
    if REPORTS_DIR.exists():
        for f in REPORTS_DIR.glob("*.md"):
            f.unlink()
        print("舊報告已刪除。")

def test_e2e_flow():
    """執行完整的端對端測試流程"""
    cleanup()

    # 1. 啟動 colab_runner.py
    print_header("步驟 1: 啟動應用程式")
    env = os.environ.copy()
    # 使用快速測試模式以加快 E2E 測試
    env["RUN_MODE"] = "快速驗證模式 (Fast-Test Mode)"

    runner_process = subprocess.Popen(
        [sys.executable, "run/colab_runner.py"],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8'
    )
    print(f"`colab_runner.py` 已在背景啟動 (PID: {runner_process.pid})")

    # 2. 等待並驗證 API 伺服器健康
    print_header("步驟 2: 驗證 API 伺服器健康")
    is_healthy = False
    for i in range(20): # 等待最多 10 秒
        try:
            response = requests.get(f"{API_BASE_URL}/api/health", timeout=1)
            if response.status_code == 200 and response.json().get("status") == "ok":
                print("✅ 健康檢查通過！")
                is_healthy = True
                break
        except requests.ConnectionError:
            time.sleep(0.5)

    if not is_healthy:
        runner_process.kill()
        stdout, _ = runner_process.communicate()
        print("\n--- colab_runner.py 輸出 ---")
        print(stdout)
        assert False, "❌ 伺服器健康檢查失敗！"

    # 3. 驗證數據 API
    print_header("步驟 3: 驗證數據 API")
    try:
        status_res = requests.get(f"{API_BASE_URL}/api/status")
        assert status_res.status_code == 200
        print("✅ /api/status 響應正常。")

        logs_res = requests.get(f"{API_BASE_URL}/api/logs")
        assert logs_res.status_code == 200
        print("✅ /api/logs 響應正常。")
    except Exception as e:
        assert False, f"❌ 請求數據 API 時發生錯誤: {e}"

    # 4. 模擬手動中斷並等待關閉
    print_header("步驟 4: 模擬手動中斷")
    runner_process.send_signal(signal.SIGINT)
    print("已發送 SIGINT 訊號，等待程序終止...")

    try:
        runner_process.wait(timeout=15)
        print("✅ `colab_runner.py` 程序已成功終止。")
    except subprocess.TimeoutExpired:
        runner_process.kill()
        stdout, stderr = runner_process.communicate()
        print("--- colab_runner.py STDOUT ---")
        print(stdout)
        print("--- colab_runner.py STDERR ---")
        print(stderr)
        assert False, "❌ 程序在發送中斷訊號後未能及時終止。"

    # 5. 驗證報告生成
    print_header("步驟 5: 驗證報告生成")
    assert REPORTS_DIR.exists(), f"❌ 報告目錄 '{REPORTS_DIR}' 未被創建！"

    reports = list(REPORTS_DIR.glob("*.md"))

    has_summary = any("綜合摘要" in f.name for f in reports)
    has_logs = any("詳細日誌" in f.name for f in reports)
    has_perf = any("詳細效能" in f.name for f in reports)

    assert has_summary, "❌ 未找到綜合摘要報告！"
    print("✅ 綜合摘要報告已生成。")
    assert has_logs, "❌ 未找到詳細日誌報告！"
    print("✅ 詳細日誌報告已生成。")
    assert has_perf, "❌ 未找到詳細效能報告！"
    print("✅ 詳細效能報告已生成。")

    print_header("🎉 E2E 測試成功！🎉")

if __name__ == "__main__":
    # 需要安裝 requests 套件來運行此測試
    try:
        import requests
    except ImportError:
        print("需要安裝 'requests' 套件。正在嘗試安裝...")
        subprocess.run([sys.executable, "-m", "pip", "install", "requests"], check=True)

    import sys
    test_e2e_flow()
