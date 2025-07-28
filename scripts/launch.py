# -*- coding: utf-8 -*-
"""
鳳凰之心專案 - 智慧啟動器 (Phoenix Heart - Smart Launcher)

用法:
  - 啟動所有服務: python scripts/launch.py
  - 顯示儀表板:  python scripts/launch.py --dashboard
  - 僅準備環境:  python scripts/launch.py --prepare-only
"""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

# --- 常數定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_PATH = PROJECT_ROOT / "src"
VENV_PATH = PROJECT_ROOT / ".venvs"
REQUIREMENTS_PATH = PROJECT_ROOT / "requirements"
APPS = {
    "quant": {"port": 8001, "status": "Not Running"},
    "transcriber": {"port": 8002, "status": "Not Running"},
}

# --- 輔助函式 ---

def print_header(title):
    """印出帶有邊框的標題"""
    print("\n" + "="*50)
    print(f" {title}")
    print("="*50)

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
        rc = process.poll()
        if rc != 0:
            print(f"❌ 命令執行失敗，返回碼: {rc}")
        return rc
    except FileNotFoundError:
        print(f"❌ 錯誤: 找不到命令 '{command[0]}'。請確保它已安裝並在系統 PATH 中。")
        return 1
    except Exception as e:
        print(f"❌ 執行命令時發生意外錯誤: {e}")
        return 1

def setup_virtualenv():
    """建立並更新共享的虛擬環境"""
    print_header("1. 設定虛擬環境")
    venv_python = VENV_PATH / "base" / "bin" / "python"
    if not venv_python.exists():
        print(f"建立新的虛擬環境於: {VENV_PATH / 'base'}")
        run_command([sys.executable, "-m", "venv", str(VENV_PATH / "base")])
    else:
        print("虛擬環境已存在。")

    # 安裝基礎依賴
    print("\n安裝/更新基礎依賴...")
    run_command([
        str(venv_python), "-m", "pip", "install", "-r",
        str(REQUIREMENTS_PATH / "base.txt")
    ])

    # 安裝各個 App 的依賴
    for app_name in APPS:
        print(f"\n安裝/更新 {app_name} 的依賴...")
        run_command([
            str(venv_python), "-m", "pip", "install", "-r",
            str(REQUIREMENTS_PATH / f"{app_name}.txt")
        ])
    print("\n✅ 環境準備完成!")
    return str(venv_python)

def start_services(python_executable, args):
    """在背景啟動所有 FastAPI 服務"""
    print_header("2. 啟動微服務")
    processes = []

    # 從命令列參數或預設值更新 App 設定
    APPS["quant"]["port"] = args.port_quant
    APPS["transcriber"]["port"] = args.port_transcriber

    for app_name, config in APPS.items():
        port = config["port"]
        print(f"啟動 {app_name} 服務於埠 {port}...")
        env = os.environ.copy()
        env["PORT"] = str(port)
        env["TIMEZONE"] = args.timezone
        # 我們需要將 src 目錄加到 PYTHONPATH，這樣 `from quant.main` 才能運作
        env["PYTHONPATH"] = str(SRC_PATH)

        process = subprocess.Popen(
            [python_executable, "-m", f"{app_name}.main"],
            cwd=SRC_PATH,
            env=env
        )
        processes.append(process)
        print(f"✅ {app_name} 服務已啟動，PID: {process.pid}")

    return processes

def start_dashboard(python_executable):
    """使用 gotty 啟動儀表板"""
    print_header("啟動儀表板")
    dashboard_script = PROJECT_ROOT / "scripts" / "phoenix_dashboard.py"
    gotty_path = PROJECT_ROOT / "tools" / "gotty"

    if not gotty_path.exists():
        print(f"❌ 錯誤: 找不到 gotty 工具於 {gotty_path}")
        print("請根據 README 指示下載它。")
        sys.exit(1)

    command = [
        str(gotty_path),
        "--port", "8080",
        "--title-format", "鳳凰之心儀表板",
        "--permit-write",
        python_executable, str(dashboard_script)
    ]
    print(f"🚀 使用 GoTTY 將儀表板網頁化於 http://localhost:8080")
    # GoTTY 會佔用前景，所以我們直接執行它
    try:
        run_command(command)
    except KeyboardInterrupt:
        print("\nGoTTY 服務已停止。")


def main():
    """主函式"""
    parser = argparse.ArgumentParser(description="鳳凰之心專案智慧啟動器")
    # 功能性參數
    parser.add_argument("--dashboard", action="store_true", help="啟動並顯示互動式儀表板")
    parser.add_argument("--prepare-only", action="store_true", help="僅設定環境和安裝依賴，然後退出")

    # 服務設定參數
    parser.add_argument("--port-quant", type=int, default=8001, help="設定 Quant 服務的埠號")
    parser.add_argument("--port-transcriber", type=int, default=8002, help="設定 Transcriber 服務的埠號")
    parser.add_argument("--timezone", type=str, default="Asia/Taipei", help="設定服務的時區")

    args = parser.parse_args()

    python_executable = setup_virtualenv()

    if args.prepare_only:
        print("\n環境準備完成，根據 --prepare-only 指示退出。")
        sys.exit(0)

    if args.dashboard:
        # 注意: 儀表板目前不支援動態埠號，它依賴於固定的內部設定
        start_dashboard(python_executable)
    else:
        processes = start_services(python_executable, args)

        def shutdown_services(signum, frame):
            print(f"\n🛑 收到訊號 {signum}，正在關閉所有服務...")
            for p in processes:
                if p.poll() is None: # 如果程序還在運行
                    p.terminate()
            # 等待所有進程終止
            for p in processes:
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print(f"PID {p.pid} 未能終止，強制結束。")
                    p.kill()
            print("✅ 所有服務已成功關閉。")
            sys.exit(0)

        # 註冊訊號處理器
        import signal
        signal.signal(signal.SIGTERM, shutdown_services)
        signal.signal(signal.SIGINT, shutdown_services)

        print_header("所有服務已在背景啟動")
        print(f"主程序 PID: {os.getpid()}。發送 SIGTERM 或 SIGINT (Ctrl+C) 到此 PID 以關閉所有服務。")

        # 保持主程序運行以等待訊號
        try:
            while True:
                # 檢查子程序狀態
                for p in processes:
                    if p.poll() is not None:
                        print(f"⚠️ 警告: 子程序 {p.args} (PID: {p.pid}) 已意外終止。")
                        # 可以在此處添加重啟邏輯
                time.sleep(10)
        except Exception as e:
            print(f"主迴圈發生錯誤: {e}")
        finally:
            shutdown_services(0, None)

if __name__ == "__main__":
    main()
