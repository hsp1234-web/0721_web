# -*- coding: utf-8 -*-
"""
鳳凰之心專案 - 智慧啟動器 v8.0 (Phoenix Heart - Smart Launcher v8.0)

此版本完全支援 `docs/ARCHITECTURE.md` 中定義的最終架構。

核心功能:
- **雙模式啟動**:
  - **標準模式**: `python scripts/launch.py` - 啟動後端服務。
  - **儀表板模式**: `python scripts/launch.py --dashboard` - 啟動互動式儀表板。
- **GoTTY 整合**: 在儀表板模式下，自動使用 GoTTY 將 TUI 儀表板 Web 化。
- **Colab IFrame 嵌入**: 在 Colab 環境中，自動將儀表板嵌入到輸出儲存格。
- **自動化環境準備**: 使用 uv 自動為每個微服務建立獨立的虛擬環境並安裝依賴。

"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
import shutil
import httpx
from IPython.display import display, IFrame

# --- 常數定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
TOOLS_DIR = PROJECT_ROOT / "tools"
REQUIREMENTS_DIR = PROJECT_ROOT / "requirements"

# --- 輔助函式 ---

def print_header(title):
    """印出帶有邊框的標題"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def find_uv_executable():
    """尋找 uv 執行檔，若無則提示安裝"""
    uv_executable = shutil.which("uv")
    if not uv_executable:
        print("❌ 錯誤: 找不到 `uv` 命令。")
        print("請先安裝 uv: `pip install uv` 或參考官方文件。")
        sys.exit(1)
    return uv_executable

def run_command(command, cwd=None, env=None):
    """執行一個 shell 命令並即時顯示輸出"""
    print(f"🚀 執行中: {' '.join(command)}")
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=cwd,
            env=env
        )
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())
                sys.stdout.flush()
        rc = process.wait()
        if rc != 0:
            print(f"❌ 命令執行失敗，返回碼: {rc}")
        return rc
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到命令 '{command[0]}'。")
        return 1
    except Exception as e:
        print(f"❌ 執行命令時發生意外錯誤: {e}")
        return 1

def prepare_app_environment(app_path: Path, uv_executable: str):
    """為單一應用程式準備獨立的虛擬環境和依賴"""
    app_name = app_path.name
    print_header(f"為 {app_name} 準備環境")

    venv_path = app_path / ".venv"
    python_executable = venv_path / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')

    # 1. 建立虛擬環境
    if not venv_path.exists():
        print(f"為 {app_name} 建立新的虛擬環境於: {venv_path}")
        run_command([uv_executable, "venv", str(venv_path), "--seed"])
    else:
        print(f"{app_name} 的虛擬環境已存在。")

    # 2. 安裝依賴
    base_reqs_file = REQUIREMENTS_DIR / "base.txt"
    app_reqs_file = REQUIREMENTS_DIR / f"{app_name}.txt"

    if base_reqs_file.exists():
        print(f"為 {app_name} 安裝基礎依賴...")
        run_command([
            uv_executable, "pip", "install",
            "--python", str(python_executable),
            "-r", str(base_reqs_file)
        ])

    if app_reqs_file.exists():
        print(f"為 {app_name} 安裝特定依賴...")
        run_command([
            uv_executable, "pip", "install",
            "--python", str(python_executable),
            "-r", str(app_reqs_file)
        ])
    else:
        print(f"⚠️ 警告: 在 {REQUIREMENTS_DIR} 中找不到 {app_name}.txt，跳過特定依賴安裝。")

    print(f"✅ {app_name} 環境準備完成!")
    return str(python_executable)

def start_services(apps_to_run):
    """在背景啟動所有 FastAPI 服務"""
    print_header("啟動所有微服務")
    processes = []

    for app_name, config in apps_to_run.items():
        port = config["port"]
        python_executable = config["python"]
        print(f"啟動 {app_name} 服務於埠 {port}...")
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["PYTHONPATH"] = str(PROJECT_ROOT)

        process = subprocess.Popen(
            [python_executable, "-m", f"src.{app_name}.main"],
            cwd=PROJECT_ROOT,
            env=env
        )
        processes.append(process)
        print(f"✅ {app_name} 服務已啟動，PID: {process.pid}")

    return processes

def start_dashboard():
    """使用 gotty 啟動儀表板"""
    print_header("啟動儀表板")
    dashboard_script = PROJECT_ROOT / "scripts" / "phoenix_dashboard.py"
    gotty_path = TOOLS_DIR / "gotty"
    dashboard_port = 8080

    if not gotty_path.exists():
        print(f"❌ 錯誤: 找不到 gotty 工具於 {gotty_path}")
        print("請根據 README 指示下載它。")
        sys.exit(1)

    command = [
        str(gotty_path),
        "--port", str(dashboard_port),
        "--title-format", "鳳凰之心儀表板",
        "--permit-write",
        sys.executable, str(dashboard_script)
    ]

    print(f"🚀 使用 GoTTY 將儀表板網頁化於 http://localhost:{dashboard_port}")

    # 在背景啟動 gotty
    gotty_process = subprocess.Popen(command)

    # 健康檢查
    print("--- 等待儀表板服務啟動 ---")
    is_colab = "google.colab" in sys.modules

    for i in range(20): # 最多等待 20 秒
        try:
            response = httpx.get(f"http://localhost:{dashboard_port}", timeout=1)
            if response.status_code == 200:
                print("✅ 儀表板服務已就緒！")
                if is_colab:
                    from google.colab.output import eval_js
                    proxy_url = eval_js(f'google.colab.kernel.proxyPort({dashboard_port})')
                    print(f"🌍 Colab 公開網址: {proxy_url}")
                    display(IFrame(proxy_url, width='100%', height=700))
                return gotty_process
        except httpx.RequestError:
            time.sleep(1)
            print(f"重試 {i+1}/20...")

    print("❌ 錯誤: 儀表板服務啟動超時。")
    gotty_process.terminate()
    return None


def main():
    """主函式"""
    parser = argparse.ArgumentParser(description="鳳凰之心專案智慧啟動器 v8.0")
    parser.add_argument("--dashboard", action="store_true", help="啟動並顯示互動式儀表板")
    args = parser.parse_args()

    uv_executable = find_uv_executable()

    apps_to_run = {}
    ports = {"quant": 8001, "transcriber": 8002}

    for app_path in SRC_DIR.iterdir():
        if app_path.is_dir() and (app_path / "main.py").exists():
            app_name = app_path.name
            python_executable = prepare_app_environment(app_path, uv_executable)
            apps_to_run[app_name] = {
                "python": python_executable,
                "path": app_path,
                "port": ports.get(app_name, 8000)
            }

    if args.dashboard:
        dashboard_process = start_dashboard()
        if dashboard_process:
            print("儀表板正在運行中。按 Ctrl+C 關閉。")
            try:
                dashboard_process.wait()
            except KeyboardInterrupt:
                print("\n🛑 正在關閉儀表板...")
                dashboard_process.terminate()
    else:
        processes = start_services(apps_to_run)

        def shutdown_services(signum, frame):
            print(f"\n🛑 收到訊號 {signum}，正在關閉所有服務...")
            for p in processes:
                if p.poll() is None:
                    p.terminate()
            for p in processes:
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"PID {p.pid} 未能終止，強制結束。")
                    p.kill()
            print("✅ 所有服務已成功關閉。")
            sys.exit(0)

        import signal
        signal.signal(signal.SIGTERM, shutdown_services)
        signal.signal(signal.SIGINT, shutdown_services)

        print_header("所有服務已在背景啟動")
        print(f"主程序 PID: {os.getpid()}。按 Ctrl+C 以關閉所有服務。")

        try:
            while True:
                for p in processes:
                    if p.poll() is not None:
                        print(f"⚠️ 警告: 子程序 {p.args} (PID: {p.pid}) 已意外終止。")
                time.sleep(10)
        except Exception as e:
            print(f"主迴圈發生錯誤: {e}")
        finally:
            shutdown_services(0, None)

if __name__ == "__main__":
    main()
