# -*- coding: utf-8 -*-
import asyncio
import subprocess
import sys
import os
import json
import time
from pathlib import Path
import psutil
from concurrent.futures import ProcessPoolExecutor

# -*- coding: utf-8 -*-
# 在匯入任何可能尚未安裝的套件之前，先安裝核心依賴
import subprocess
import sys
from pathlib import Path

# --- 核心依賴安裝 ---
# 這是為了確保 runner 本身可以順利運行
runner_reqs = Path(__file__).parent / "requirements.txt"
subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(runner_reqs)], check=True)

import asyncio
import os
import json
import time
import psutil
from concurrent.futures import ProcessPoolExecutor


# --- 全域設定 ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
APPS_DIR = PROJECT_ROOT / "apps"
CONFIG_FILE = PROJECT_ROOT / "config" / "services.json"

def log(level, service, message, **kwargs):
    """標準化的 JSON 日誌輸出"""
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level,
        "service": service,
        "message": message,
        **kwargs
    }
    print(json.dumps(log_entry, ensure_ascii=False))

def install_and_launch(service_config):
    """
    安裝單一服務的依賴並啟動它。
    這個函式將在獨立的進程中執行。
    """
    name = service_config["name"]
    path = Path(service_config["path"])
    entrypoint = service_config["entrypoint"]
    port = service_config["port"]
    requirements = Path(service_config["requirements"])

    # 建立虛擬環境
    venv_path = path / "venv"
    log("INFO", name, f"正在建立虛擬環境於 {venv_path}...")
    subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True)

    # 安裝依賴
    pip_path = venv_path / "bin" / "pip"
    log("INFO", name, f"正在從 {requirements} 安裝依賴...")
    subprocess.run([str(pip_path), "install", "-r", str(requirements)], check=True, capture_output=True)

    # 啟動服務
    python_path = venv_path / "bin" / "python"
    log("INFO", name, f"正在從 {entrypoint} 啟動服務於通訊埠 {port}...")
    env = os.environ.copy()
    env["PORT"] = str(port)
    # 使用 Popen 以非阻塞方式啟動
    process = subprocess.Popen([str(python_path), entrypoint], cwd=path, env=env)

    # 向 API Gateway 報告狀態
    import requests
    try:
        requests.post("http://localhost:8000/report_status", params={"service": name, "status": "online"})
    except requests.exceptions.RequestException as e:
        log("WARNING", name, f"無法向 API Gateway 報告狀態: {e}")

    log("SUCCESS", name, f"服務已成功啟動，進程 ID: {process.pid}")
    return name, "online"


async def main():
    """
    分階段啟動的主編排器
    """
    log("INFO", "orchestrator", "系統啟動程序開始...")

    # --- 階段一：核心服務啟動 ---
    log("INFO", "orchestrator", "--- 階段一：啟動核心服務 ---")

    # 啟動 API Server
    log("INFO", "orchestrator", "正在安裝 API 伺服器依賴...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(APPS_DIR / "api_server" / "requirements.txt")], check=True, capture_output=True)

    log("INFO", "orchestrator", "正在啟動 API 伺服器...")
    api_server_process = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
        cwd=APPS_DIR / "api_server"
    )
    log("SUCCESS", "api_server", f"核心 API 伺服器已啟動，進程 ID: {api_server_process.pid}")

    # 在背景啟動資源監控腳本
    log("INFO", "orchestrator", "正在啟動高頻資源監控...")
    monitor_process = subprocess.Popen(
        [sys.executable, str(PROJECT_ROOT / "utils" / "resource_monitor.py"), "5"], # 每 5 秒監控一次
        stdout=sys.stdout, # 將監控日誌直接導向主進程的 stdout
        stderr=subprocess.STDOUT
    )

    log("INFO", "orchestrator", "--- 核心服務已上線，準備進入階段二 ---")

    # --- 階段二：非同步載入業務服務 ---
    log("INFO", "orchestrator", "--- 階段二：非同步載入業務服務 ---")

    try:
        with open(CONFIG_FILE, "r") as f:
            services_to_launch = json.load(f)["services"]
    except FileNotFoundError:
        log("CRITICAL", "orchestrator", f"找不到服務設定檔: {CONFIG_FILE}")
        return

    # 使用 ProcessPoolExecutor 來平行執行安裝與啟動任務
    with ProcessPoolExecutor() as executor:
        loop = asyncio.get_event_loop()
        tasks = [
            loop.run_in_executor(executor, install_and_launch, config)
            for config in services_to_launch
        ]

        for future in asyncio.as_completed(tasks):
            try:
                service_name, status = await future
                log("SUCCESS", "orchestrator", f"業務服務 '{service_name}' 已成功上線。")
            except Exception as e:
                log("ERROR", "orchestrator", f"啟動某個業務服務時發生嚴重錯誤: {e}")

    log("INFO", "orchestrator", "所有業務服務啟動程序已完成。")

    # 保持主程序運行，等待手動中斷
    try:
        # 一個簡單的方法讓主程序保持運行
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        log("INFO", "orchestrator", "主程序被取消。")
    finally:
        log("INFO", "orchestrator", "正在關閉所有服務...")
        monitor_process.terminate()
        api_server_process.terminate()
        # 在這裡還應該有關閉所有業務服務的邏輯
        await monitor_process.wait()
        await api_server_process.wait()
        log("INFO", "orchestrator", "系統已關閉。")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log("INFO", "orchestrator", "偵測到手動中斷，系統正在關閉...")
