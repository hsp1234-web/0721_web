# -*- coding: utf-8 -*-
import asyncio
import subprocess
import sys
import json
from pathlib import Path
import os
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import Response
import uvicorn
import time

# --- 共享狀態管理 ---
STATE_FILE = Path(os.getenv("STATE_FILE", "/tmp/phoenix_state.json"))
_state = {"apps": {}, "overall_status": "starting", "show_action_button": False}

def update_state_file():
    """將當前狀態原子化地寫入 JSON 檔案"""
    # 檢查所有 App 是否都已運行
    all_running = all(details.get("status") == "running" for details in _state["apps"].values())
    if all_running and len(_state["apps"]) >= 2: # 假設至少有 quant 和 transcriber
        _state["overall_status"] = "all_running"
        _state["show_action_button"] = True

    with open(STATE_FILE, 'w') as f:
        json.dump(_state, f)

def set_app_status(app_name, status):
    if app_name not in _state["apps"]:
        _state["apps"][app_name] = {}
    _state["apps"][app_name]["status"] = status
    update_state_file()

# --- 顏色代碼 ---
class colors:
    HEADER = '\033[95m'; OKCYAN = '\033[96m'; OKGREEN = '\033[92m'; WARNING = '\033[93m'; FAIL = '\033[91m'; ENDC = '\033[0m'; BOLD = '\033[1m'

def print_header(message): print(f"\n{colors.HEADER}{colors.BOLD}🚀 {message} 🚀{colors.ENDC}")
def print_success(message): print(f"{colors.OKGREEN}✅ {message}{colors.ENDC}")
def print_warning(message): print(f"{colors.WARNING}⚠️ {message}{colors.ENDC}")
def print_info(message): print(f"{colors.OKCYAN}ℹ️ {message}{colors.ENDC}")

# 導入 safe_installer
from core_utils.safe_installer import install_packages

async def prepare_app(app_path: Path):
    app_name = app_path.name
    set_app_status(app_name, "starting")
    print_header(f"正在準備 App: {app_name}")
    # ... (prepare_app 的其餘部分不變)
    venv_path = app_path / ".venv"
    requirements_path = app_path / "requirements.txt"
    if not requirements_path.exists():
        print_warning(f"在 {app_name} 中找不到 requirements.txt，跳過。")
        set_app_status(app_name, "running") # 沒有依賴，視為直接成功
        return
    python_executable = venv_path / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    subprocess.run(f"uv venv", cwd=app_path, shell=True, capture_output=True)
    install_packages(app_name, str(requirements_path), str(python_executable))
    print_success(f"[{app_name}] 所有依賴已成功安裝。")

async def launch_app(app_path: Path, port: int):
    app_name = app_path.name
    print_header(f"正在啟動 App: {app_name}")
    venv_python = str(app_path / (".venv/Scripts/python" if sys.platform == "win32" else ".venv/bin/python"))
    main_py_path = str(app_path / "main.py")
    env = os.environ.copy()
    env["PYTHONPATH"] = str(Path(__file__).parent.resolve())
    env["PORT"] = str(port)
    subprocess.Popen([venv_python, main_py_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, env=env)

    # 簡單的健康檢查，確認服務是否真的啟動
    await asyncio.sleep(3) # 給予啟動時間
    try:
        async with httpx.AsyncClient() as client:
            # 假設所有 App 根目錄都有一個 health check
            response = await client.get(f"http://localhost:{port}/", timeout=2)
            if response.status_code == 200 or response.status_code == 404: # 404 也可能代表服務器在運行但無此路由
                 set_app_status(app_name, "running")
                 print_success(f"App '{app_name}' 已在背景啟動並通過健康檢查。")
            else:
                raise Exception("Health check failed")
    except Exception:
        set_app_status(app_name, "failed")
        print_warning(f"App '{app_name}' 可能啟動失敗。")


async def main():
    print_header("鳳凰之心專案啟動程序開始")
    # 初始化狀態檔案
    update_state_file()

    # ... (ensure_uv_installed, ensure_core_deps 的呼叫保持不變) ...
    apps_to_launch = [d for d in APPS_DIR.iterdir() if d.is_dir() and d.name != 'dashboard_api']

    for app_path in apps_to_launch:
        await prepare_app(app_path)

    port_map = {'quant': 8001, 'transcriber': 8002}
    for app_path in apps_to_launch:
        await launch_app(app_path, port_map.get(app_path.name))

    print_success("所有 App 啟動程序已完成。")
    # 保持 launch.py 運行一段時間以供 dashboard_api 讀取最終狀態
    # 在真實部署中，這裡可能是一個無限循環或由 supervisor 管理
    time.sleep(60)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        _state["overall_status"] = "failed"
        _state["error_message"] = str(e)
        update_state_file()
        print(f"{colors.FAIL}\n啟動過程中發生未預期的嚴重錯誤: {e}{colors.ENDC}")
        sys.exit(1)
