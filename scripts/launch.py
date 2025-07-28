# -*- coding: utf-8 -*-
"""
鳳凰之心專案 - 智慧啟動器 (Phoenix Heart - Smart Launcher)

一份腳本，統御所有環境。
無論是在本地 Ubuntu 開發，或是在 Google Colab 演示，皆可由此單一入口啟動。

用法:
  - 啟動所有微服務:
    python scripts/launch.py

  - 在 Colab / 本地無縫啟動並顯示儀表板:
    python scripts/launch.py --dashboard

  - 僅準備環境 (安裝依賴):
    python scripts/launch.py --prepare-only
"""
import argparse
import os
import subprocess
import sys
import time
import socket
from pathlib import Path
from urllib.request import urlopen

# --- 常數定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
VENV_PATH = PROJECT_ROOT / ".venvs" / "phoenix_heart"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements"
APPS = {
    "quant": {"port": 8001, "status": "Not Running", "process": None},
    "transcriber": {"port": 8002, "status": "Not Running", "process": None},
}
DASHBOARD_PORT = 8080

# --- 環境偵測與輔助函式 ---

def is_in_colab():
    """透過檢查環境變數判斷是否在 Google Colab 環境中"""
    return "COLAB_GPU" in os.environ

def print_header(title):
    """印出帶有風格的標題"""
    print("\n" + "🚀" * 25)
    print(f"  {title}")
    print("=" * 55)

def run_command(command, cwd=None, env=None, capture=False):
    """
    執行一個 shell 命令。
    :param command: 命令列表。
    :param capture: 若為 True，則返回 stdout，否則即時印出。
    """
    print(f"🏃 執行中: {' '.join(command)}")
    try:
        if not capture:
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
            rc = process.poll()
            if rc != 0:
                print(f"❌ 命令執行失敗，返回碼: {rc}")
            return rc
        else:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=cwd,
                env=env
            )
            if result.returncode != 0:
                print(f"❌ 命令執行失敗，返回碼: {result.returncode}")
                print(result.stderr)
            return result
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到命令 '{command[0]}'。請確保它已安裝並在系統 PATH 中。")
        return 1 if not capture else None
    except Exception as e:
        print(f"❌ 執行命令時發生意外錯誤: {e}")
        return 1 if not capture else None

def prepare_environment():
    """
    準備執行環境。
    在 Colab 中，直接安裝到全域。
    在本地，則建立一個獨立的虛擬環境。
    """
    print_header("1. 準備執行環境")

    if is_in_colab():
        print("🔍 偵測到 Colab 環境，將在全域環境中安裝依賴。")
        python_executable = sys.executable
        pip_command_base = [python_executable, "-m", "pip", "install", "-r"]

        # 安裝所有依賴
        for req_file in REQUIREMENTS_PATH.glob("*.txt"):
            print(f"\n📄 安裝依賴從: {req_file.name}")
            run_command(pip_command_base + [str(req_file)])

        print("\n✅ Colab 環境準備完成!")
        return python_executable
    else:
        print("🔍 偵測到本地環境，將設定獨立虛擬環境。")
        venv_python = VENV_PATH / "bin" / "python"
        if not venv_python.exists():
            print(f"🌱 建立新的虛擬環境於: {VENV_PATH}")
            run_command([sys.executable, "-m", "venv", str(VENV_PATH)])
        else:
            print("🌳 虛擬環境已存在。")

        pip_command_base = [str(venv_python), "-m", "pip", "install", "-r"]

        # 安裝所有依賴
        for req_file in REQUIREMENTS_PATH.glob("*.txt"):
            print(f"\n📄 安裝依賴從: {req_file.name}")
            run_command(pip_command_base + [str(req_file)])

        print("\n✅ 本地虛擬環境準備完成!")
        return str(venv_python)

def start_services(python_executable, args):
    """在背景啟動所有微服務"""
    print_header("2. 啟動微服務")

    APPS["quant"]["port"] = args.port_quant
    APPS["transcriber"]["port"] = args.port_transcriber

    for app_name, config in APPS.items():
        port = config["port"]
        print(f"🔥 啟動 {app_name} 服務於埠 {port}...")
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["TIMEZONE"] = args.timezone
        env["PYTHONPATH"] = str(SRC_PATH)

        process = subprocess.Popen(
            [python_executable, "-m", f"{app_name}.main"],
            cwd=SRC_PATH,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
        )
        APPS[app_name]["process"] = process
        print(f"✅ {app_name} 服務已啟動 (PID: {process.pid})")

def wait_for_service(port, timeout=30):
    """等待直到指定的埠號上的服務可用"""
    print(f"⏳ 等待埠 {port} 上的服務啟動...")
    start_time = time.monotonic()
    while time.monotonic() - start_time < timeout:
        try:
            with socket.create_connection(("localhost", port), timeout=1):
                print(f"✅ 埠 {port} 上的服務已就緒！")
                return True
        except (socket.timeout, ConnectionRefusedError):
            time.sleep(0.5)
    print(f"❌ 等待服務超時 (埠 {port})。")
    return False

def start_dashboard_colab(python_executable):
    """專為 Colab 設計的儀表板啟動流程"""
    print_header("啟動儀表板 (Colab 模式)")
    gotty_path = PROJECT_ROOT / "tools" / "gotty"
    dashboard_script = PROJECT_ROOT / "scripts" / "phoenix_dashboard.py"

    if not gotty_path.exists():
        print(f"❌ 錯誤: 找不到 GoTTY 工具於 {gotty_path}。請確保它已存在。")
        sys.exit(1)

    # 確保 gotty 有執行權限
    run_command(["chmod", "+x", str(gotty_path)])

    command = [
        str(gotty_path),
        "--port", str(DASHBOARD_PORT),
        "--title-format", "鳳凰之心指揮中心",
        "--permit-write",
        python_executable, str(dashboard_script)
    ]

    print("🚀 使用 GoTTY 將儀表板串流至網頁...")
    # 在背景啟動 gotty
    gotty_process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    # 智慧重試機制：等待 gotty 服務就緒
    if wait_for_service(DASHBOARD_PORT):
        print("🌐 服務已就緒，正在生成 Colab 內嵌畫面...")
        from google.colab.output import serve_kernel_port_as_iframe
        # 將儀表板直接嵌入輸出格
        serve_kernel_port_as_iframe(DASHBOARD_PORT, width=1000, height=800)
        return gotty_process
    else:
        print("💀 無法啟動儀表板 Web 服務，請檢查 GoTTY 或腳本錯誤。")
        gotty_process.kill()
        return None

def start_dashboard_local(python_executable):
    """本地環境的儀表板啟動流程"""
    print_header("啟動儀表板 (本地模式)")
    gotty_path = PROJECT_ROOT / "tools" / "gotty"
    dashboard_script = PROJECT_ROOT / "scripts" / "phoenix_dashboard.py"

    if not gotty_path.exists():
        print(f"❌ 錯誤: 找不到 GoTTY 工具於 {gotty_path}。")
        sys.exit(1)

    # 確保 gotty 有執行權限
    run_command(["chmod", "+x", str(gotty_path)])

    command = [
        str(gotty_path),
        "--port", str(DASHBOARD_PORT),
        "--title-format", "鳳凰之心指揮中心",
        "--permit-write",
        python_executable, str(dashboard_script)
    ]

    print(f"🖥️  請在瀏覽器中開啟: http://localhost:{DASHBOARD_PORT}")
    print("   (使用 Ctrl+C 停止服務)")
    try:
        # 在前景執行，直到使用者中斷
        run_command(command)
    except KeyboardInterrupt:
        print("\n gracefully shutting down...")

def main():
    """主函式，專案的統一入口點"""
    parser = argparse.ArgumentParser(
        description="鳳凰之心專案智慧啟動器",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--dashboard", action="store_true", help="啟動並顯示互動式儀表板。\n在 Colab 中會自動嵌入畫面，在本地則提供網址。")
    parser.add_argument("--prepare-only", action="store_true", help="僅設定環境和安裝依賴，然後退出。")
    parser.add_argument("--port-quant", type=int, default=8001, help="設定 Quant 服務的埠號。")
    parser.add_argument("--port-transcriber", type=int, default=8002, help="設定 Transcriber 服務的埠號。")
    parser.add_argument("--timezone", type=str, default="Asia/Taipei", help="設定服務的時區。")
    args = parser.parse_args()

    python_executable = prepare_environment()

    if args.prepare_only:
        print("\n✅ 環境準備完成，根據 --prepare-only 指示退出。")
        sys.exit(0)

    # 啟動微服務 (儀表板也需要它們在背景運行)
    start_services(python_executable, args)

    if args.dashboard:
        if is_in_colab():
            dashboard_process = start_dashboard_colab(python_executable)
            if not dashboard_process:
                sys.exit(1)
        else:
            start_dashboard_local(python_executable) # 這個會佔用前景
            # 當本地儀表板結束時，順便關閉其他服務

    print_header("所有服務已在背景啟動")
    print(f"主程序 PID: {os.getpid()}。")

    # 保持主程序運行，監控服務狀態
    try:
        while True:
            for app_name, config in APPS.items():
                p = config.get("process")
                if p and p.poll() is not None:
                    print(f"⚠️ 警告: {app_name} 服務 (PID: {p.pid}) 已意外終止。")
                    # 可以在此處添加重啟邏輯
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n🛑 收到 Ctrl+C，正在關閉所有服務...")
    finally:
        for app_name, config in APPS.items():
            p = config.get("process")
            if p and p.poll() is None:
                print(f"🔪 正在終止 {app_name} (PID: {p.pid})...")
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    p.kill()
        print("✅ 所有服務已成功關閉。")

if __name__ == "__main__":
    main()
