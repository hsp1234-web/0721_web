# -*- coding: utf-8 -*-
"""
唯一的整合測試腳本 (The One Test Script to Rule Them All)

本腳本負責對「鳳凰之心」專案進行全面的、端到端的整合測試。
它旨在驗證我們新的「分階段啟動」架構的各個方面，包括：
- 核心服務的快速啟動
- 業務服務的平行、非同步載入
- 系統在部分服務失敗時的容錯能力
- 標準化的 JSON 日誌輸出
- API 閘道的功能
"""
import subprocess
import sys
import os
import json
import time
from pathlib import Path
import requests
import pytest

# --- 測試設定 ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
BACKEND_RUNNER_PATH = PROJECT_ROOT / "run" / "backend_runner.py"
API_BASE_URL = "http://localhost:8000"

# 安裝測試本身需要的依賴
subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(PROJECT_ROOT / "run" / "requirements.txt")], check=True)

def start_backend_runner():
    """在背景啟動 backend_runner.py 並回傳其進程物件"""
    process = subprocess.Popen(
        [sys.executable, str(BACKEND_RUNNER_PATH)],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8'
    )
    return process

def get_logs(process, timeout=30):
    """從進程的 stdout 中讀取並解析 JSON 日誌"""
    logs = []
    start_time = time.time()
    while time.time() - start_time < timeout:
        line = process.stdout.readline()
        if not line:
            # 如果沒有輸出，檢查進程是否已經結束
            if process.poll() is not None:
                break
            time.sleep(0.1)
            continue
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            print(f"警告：無法解析日誌行: {line.strip()}")
    return logs

def test_full_system_startup_and_shutdown():
    """
    測試案例 1: 驗證完整的系統啟動、狀態回報和正常關閉
    """
    print("\n--- 測試：完整系統啟動 ---")

    # 1. 啟動後端
    backend_process = start_backend_runner()

    # 2. 驗證核心服務 (API Gateway) 是否快速上線
    is_api_gw_up = False
    for _ in range(10): # 等待最多 5 秒
        try:
            response = requests.get(API_BASE_URL + "/", timeout=1)
            if response.status_code == 200:
                is_api_gw_up = True
                print("✅ API Gateway 已上線")
                break
        except requests.ConnectionError:
            time.sleep(0.5)

    if not is_api_gw_up:
        # 測試失敗時，印出所有日誌以供偵錯
        stdout, _ = backend_process.communicate(timeout=5)
        print("\n--- 後端日誌輸出 ---")
        print(stdout)
        pytest.fail("❌ API Gateway 未能在預期時間內啟動")

    # 3. 驗證業務服務是否都成功上線
    online_services = set()
    for _ in range(60): # 給予足夠的時間 (60s) 讓服務安裝和啟動
        try:
            response = requests.get(API_BASE_URL + "/status", timeout=1)
            if response.status_code == 200:
                status_data = response.json()
                current_online = {svc for svc, stat in status_data.items() if stat == "online"}
                if len(current_online) == 2: # 假設有 quant 和 transcriber 兩個服務
                    online_services = current_online
                    print(f"✅ 所有業務服務都已上線: {online_services}")
                    break
        except requests.ConnectionError:
            pass
        time.sleep(1)

    assert online_services == {"quant", "transcriber"}, f"❌ 不是所有的業務服務都成功上線，線上服務: {online_services}"

    # 4. 關閉後端並收集日誌
    print("--- 正在關閉後端 ---")
    backend_process.terminate()

    # 等待進程結束並獲取其輸出
    stdout, _ = backend_process.communicate(timeout=10)

    # 處理剩餘的日誌
    logs = []
    for line in stdout.splitlines():
        try:
            logs.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    print(f"--- 總共收集到 {len(logs)} 條日誌 ---")

    # 5. 驗證日誌內容
    assert any(l.get("service") == "orchestrator" and l.get("level") == "INFO" for l in logs), "❌ 缺少 orchestrator 的啟動日誌"
    assert any(l.get("service") == "api_server" and l.get("level") == "SUCCESS" for l in logs), "❌ 缺少 api_server 的成功日誌"
    assert any(l.get("service") == "quant" and l.get("level") == "SUCCESS" for l in logs), "❌ 缺少 quant 的成功日誌"
    assert any(l.get("service") == "transcriber" and l.get("level") == "SUCCESS" for l in logs), "❌ 缺少 transcriber 的成功日誌"
    assert any(l.get("service") == "system_monitor" for l in logs), "❌ 缺少 system_monitor 的效能日誌"

    print("✅ 完整系統啟動測試通過！")

# 之後會在這裡添加容錯測試
