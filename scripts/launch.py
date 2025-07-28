# -*- coding: utf-8 -*-
"""
鳳凰之心專案 - 智慧啟動器 v2.0 (Phoenix Heart - Smart Launcher v2.0)

此版本完全支援 `docs/ARCHITECTURE.md` 中定義的最終架構。

核心功能:
- **獨立虛擬環境**: 為 `apps/` 下的每個應用程式自動建立和管理獨立的 `.venv`。
- **uv 加速**: 使用 `uv` 來極速建立環境和安裝依賴。
- **智慧啟動**: 啟動所有應用程式，並可選擇性地啟動儀表板。
- **環境一致性**: 確保在任何環境下都能有一致的啟動體驗。

用法:
  - 啟動所有服務: python scripts/launch.py
  - 顯示儀表板:  python scripts/launch.py --dashboard
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path
import shutil

# --- 常數定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS_DIR = PROJECT_ROOT / "apps"

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
        for line in iter(process.stdout.readline, ''):
            print(line.strip())
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
    reqs_file = app_path / "requirements.txt"

    # 1. 建立虛擬環境
    if not venv_path.exists():
        print(f"為 {app_name} 建立新的虛擬環境於: {venv_path}")
        run_command([uv_executable, "venv", str(venv_path), "--seed"])
    else:
        print(f"{app_name} 的虛擬環境已存在。")

    # 2. 安裝依賴
    if reqs_file.exists():
        print(f"為 {app_name} 安裝/更新依賴...")
        run_command([
            uv_executable, "pip", "install",
            "--python", str(python_executable),
            "-r", str(reqs_file)
        ])
    else:
        print(f"⚠️ 警告: 在 {app_path} 中找不到 requirements.txt，跳過依賴安裝。")

    print(f"✅ {app_name} 環境準備完成!")
    return str(python_executable)

def start_services(apps_to_run, args):
    """在背景啟動所有 FastAPI 服務"""
    print_header("啟動所有微服務")
    processes = []

    for app_name, config in apps_to_run.items():
        port = config["port"]
        python_executable = config["python"]
        app_dir = config["path"]

        print(f"啟動 {app_name} 服務於埠 {port}...")
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["PYTHONPATH"] = str(PROJECT_ROOT) # 讓 import aoo.quant 這樣可以運作

        process = subprocess.Popen(
            [python_executable, "-m", f"apps.{app_name}.main"],
            cwd=PROJECT_ROOT, # 從根目錄執行
            env=env
        )
        processes.append(process)
        print(f"✅ {app_name} 服務已啟動，PID: {process.pid}")

    return processes

def start_dashboard():
    """使用 gotty 啟動儀表板"""
    print_header("啟動儀表板")
    dashboard_script = PROJECT_ROOT / "scripts" / "phoenix_dashboard.py"
    gotty_path = PROJECT_ROOT / "tools" / "gotty"

    if not gotty_path.exists():
        print(f"❌ 錯誤: 找不到 gotty 工具於 {gotty_path}")
        print("請根據 README 指示下載它。")
        sys.exit(1)

    # 儀表板需要一個 python 環境來執行，我們使用其中一個 App 的環境
    # 或者可以建立一個共享的 dashboard venv
    # 為了簡單起見，我們假設儀表板的依賴已包含在 base.txt 中
    # 並使用系統 python 來啟動
    python_to_run_dashboard = sys.executable

    command = [
        str(gotty_path),
        "--port", "8080",
        "--title-format", "鳳凰之心儀表板",
        "--permit-write",
        python_to_run_dashboard, str(dashboard_script)
    ]
    print(f"🚀 使用 GoTTY 將儀表板網頁化於 http://localhost:8080")
    try:
        # 使用 run_command 以便在 CI/CD 環境中也能正常顯示輸出
        run_command(command)
    except KeyboardInterrupt:
        print("\nGoTTY 服務已停止。")


def main():
    """主函式"""
    parser = argparse.ArgumentParser(description="鳳凰之心專案智慧啟動器 v2.0")
    parser.add_argument("--dashboard", action="store_true", help="啟動並顯示互動式儀表板")
    args = parser.parse_args()

    uv_executable = find_uv_executable()

    apps_to_run = {}
    # 預設埠號
    ports = {"quant": 8001, "transcriber": 8002}

    for app_path in APPS_DIR.iterdir():
        if app_path.is_dir():
            app_name = app_path.name
            python_executable = prepare_app_environment(app_path, uv_executable)
            apps_to_run[app_name] = {
                "python": python_executable,
                "path": app_path,
                "port": ports.get(app_name, 8000) # 給個預設值
            }

    if args.dashboard:
        start_dashboard()
    else:
        processes = start_services(apps_to_run, args)

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
