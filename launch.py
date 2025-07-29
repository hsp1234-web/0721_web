# -*- coding: utf-8 -*-
"""
🚀 PHOENIX HEART PROJECT - 總開關 (Master Launcher) 🚀

這不僅僅是一個腳本，它是整個微服務架構的指揮官。
它負責協調所有 App 的環境建立、依賴安裝與啟動，並在最後啟動逆向代理，
為所有服務提供一個統一的流量入口。

執行方式:
    python launch.py
"""
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

# --- 常數與設定 ---
APPS_DIR = Path("apps")
PROXY_CONFIG_FILE = Path("proxy/proxy_config.json")
BASE_PORT = 8001

# --- 顏色代碼，讓輸出更美觀 ---
class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """打印帶有標題格式的訊息"""
    print(f"\n{colors.HEADER}{colors.BOLD}🚀 {message} 🚀{colors.ENDC}")

def print_success(message):
    """打印成功的訊息"""
    print(f"{colors.OKGREEN}✅ {message}{colors.ENDC}")

def print_warning(message):
    """打印警告訊息"""
    print(f"{colors.WARNING}⚠️ {message}{colors.ENDC}")

def print_info(message):
    """打印一般資訊"""
    print(f"{colors.OKCYAN}ℹ️ {message}{colors.ENDC}")

def run_command(command, cwd, venv_path=None):
    """執行一個子進程命令，並即時串流其輸出"""
    executable = command.split()[0]
    if venv_path:
        # 在 Windows 和 Linux/macOS 上尋找虛擬環境中的可執行檔
        bin_dir = "Scripts" if sys.platform == "win32" else "bin"
        executable_path = venv_path / bin_dir / executable
        if executable_path.exists():
            command = command.replace(executable, str(executable_path), 1)

    print_info(f"在 '{cwd}' 中執行: {colors.BOLD}{command}{colors.ENDC}")
    process = subprocess.Popen(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"   {output.strip()}")

    return_code = process.wait()
    if return_code != 0:
        raise subprocess.CalledProcessError(return_code, command)

# 導入新模組
from core_utils.safe_installer import install_packages

def ensure_uv_installed():
    """確保 uv 已經安裝"""
    print_header("檢查核心工具 uv")
    try:
        subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
        print_success("uv 已安裝。")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("uv 未找到，正在嘗試使用 pip 安裝...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "uv"])
            print_success("uv 安裝成功！")
        except subprocess.CalledProcessError as e:
            print(f"{colors.FAIL}uv 安裝失敗: {e}{colors.ENDC}")
            sys.exit(1)

def ensure_core_deps():
    """確保核心依賴 (psutil, pyyaml) 已安裝"""
    print_header("檢查核心依賴 (psutil, PyYAML)")
    try:
        import psutil
        import yaml
        print_success("核心依賴已滿足。")
    except ImportError:
        print_warning("缺少核心依賴，正在嘗試安裝...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "pyyaml"])
            print_success("核心依賴安裝成功！")
        except subprocess.CalledProcessError as e:
            print(f"{colors.FAIL}核心依賴安裝失敗: {e}{colors.ENDC}")
            sys.exit(1)

async def prepare_app(app_path: Path):
    """為單個 App 準備環境和依賴"""
    app_name = app_path.name
    print_header(f"正在準備 App: {app_name}")

    venv_path = app_path / ".venv"
    requirements_path = app_path / "requirements.txt"
    python_executable = venv_path / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")

    if not requirements_path.exists():
        print_warning(f"在 {app_name} 中找不到 requirements.txt，跳過依賴安裝。")
        return

    try:
        # 步驟 1: 建立虛擬環境
        print_info(f"[{app_name}] 建立或驗證虛擬環境...")
        run_command(f"uv venv", cwd=app_path)
        print_success(f"[{app_name}] 虛擬環境準備就緒。")

        # 步驟 2: 使用 safe_installer 安全安裝依賴
        print_info(f"[{app_name}] 啟動智慧型安全安裝程序...")
        install_packages(app_name, str(requirements_path), str(python_executable))
        print_success(f"[{app_name}] 所有依賴已成功安裝。")

    except (subprocess.CalledProcessError, SystemExit) as e:
        print(f"{colors.FAIL}[{app_name}] 環境準備失敗: {e}{colors.ENDC}")
        raise

async def launch_app(app_path: Path, port: int):
    """在背景啟動一個 App"""
    app_name = app_path.name
    print_header(f"正在啟動 App: {app_name}")

    venv_python = str(app_path / (".venv/Scripts/python" if sys.platform == "win32" else ".venv/bin/python"))
    main_py_path = str(app_path / "main.py")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(APPS_DIR.parent.resolve())
    env["PORT"] = str(port)

    process = subprocess.Popen(
        [venv_python, main_py_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=env
    )
    print_success(f"App '{app_name}' 已在背景啟動，監聽埠: {port}, PID: {process.pid}")
    return process

# --- 逆向代理 ---
# 讀取代理設定
with open(PROXY_CONFIG_FILE) as f:
    proxy_config = json.load(f)

proxy_app = FastAPI()
client = httpx.AsyncClient()

@proxy_app.api_route("/{path:path}")
async def reverse_proxy(request: Request):
    path = f"/{request.path_params['path']}"

    # 根據路徑前綴找到目標服務
    target_url = None
    for prefix, route_info in proxy_config["routes"].items():
        if path.startswith(prefix):
            target_host = route_info["target"]
            # 移除前綴，得到子路徑
            sub_path = path[len(prefix):]
            target_url = f"{target_host}{sub_path}"
            break

    if not target_url:
        return Response(content="無法路由的請求。", status_code=404)

    # 建立一個新的請求，轉發到目標服務
    url = httpx.URL(url=target_url, query=request.url.query.encode("utf-8"))
    headers = dict(request.headers)
    # httpx 會自動處理 host，所以從 header 中移除
    headers.pop("host", None)

    rp_req = client.build_request(
        method=request.method,
        url=url,
        headers=headers,
        content=await request.body()
    )

    try:
        rp_resp = await client.send(rp_req)
        return Response(
            content=rp_resp.content,
            status_code=rp_resp.status_code,
            headers=dict(rp_resp.headers)
        )
    except httpx.ConnectError as e:
        error_message = f"無法連接到後端服務: {target_url}。請確認該服務是否已成功啟動。"
        print(f"{colors.FAIL}{error_message}{colors.ENDC}")
        return Response(content=error_message, status_code=503) # 503 Service Unavailable

async def main():
    """主協調函式"""
    print_header("鳳凰之心專案啟動程序開始")
    ensure_uv_installed()
    ensure_core_deps()

    apps_to_launch = [d for d in APPS_DIR.iterdir() if d.is_dir()]

    # 準備所有 App 的環境
    for app_path in apps_to_launch:
        await prepare_app(app_path)

    print_success("所有 App 環境均已準備就緒！")

    # 啟動所有 App
    processes = []
    current_port = BASE_PORT
    for app_path in apps_to_launch:
        process = await launch_app(app_path, current_port)
        processes.append(process)
        current_port += 1

    # 啟動逆向代理
    listen_port = proxy_config["listen_port"]
    print_header(f"所有 App 已在背景啟動，正在啟動主逆向代理...")
    print_success(f"系統已就緒！統一訪問入口: http://localhost:{listen_port}")
    print_info(f"  - 量化服務請訪問: http://localhost:{listen_port}/quant/...")
    print_info(f"  - 轉寫服務請訪問: http://localhost:{listen_port}/transcriber/...")
    print_warning("按 Ctrl+C 終止所有服務。")

    try:
        config = uvicorn.Config(proxy_app, host="0.0.0.0", port=listen_port, log_level="warning")
        server = uvicorn.Server(config)
        await server.serve()

    except (KeyboardInterrupt, asyncio.CancelledError):
        print("\n" + colors.WARNING + "收到關閉信號..." + colors.ENDC)

    finally:
        print_info("正在終止所有背景 App 行程...")
        for p in processes:
            p.terminate()
        # 等待所有行程終止
        for p in processes:
            p.wait()
        print_success("所有服務已成功關閉。再會！")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"{colors.FAIL}\n啟動過程中發生未預期的嚴重錯誤: {e}{colors.ENDC}")
        sys.exit(1)
