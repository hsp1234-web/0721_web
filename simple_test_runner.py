# ==============================================================================
#                 核心服務簡易整合測試腳本 (v1.0)
#
#   **目標**: 直接、高效地驗證核心服務 (`server_main.py`) 的穩定性，
#             完全繞過複雜的 `colab_run.py`。
#
#   **驗證流程**:
#   1.  建立全新虛擬環境並安裝依賴。
#   2.  直接啟動 `server_main.py` 作為子進程。
#   3.  透過 HTTP API 驗證服務是否成功運行。
#   4.  使用 `psutil` 乾淨地終止服務進程樹。
#   5.  清理所有測試產生的檔案和目錄。
#   6.  若成功，腳本自我刪除。
# ==============================================================================

import os
import sys
import subprocess
import time
import shutil
import httpx
import psutil
from pathlib import Path

# --- 全域設定 ---
PROJECT_ROOT = Path(__file__).resolve().parent
VENV_DIR = PROJECT_ROOT / ".test_venv_simple"
TEST_SCRIPT_PATH = Path(__file__).resolve()
SERVICE_URL = "http://127.0.0.1:8000/quant/data"
STARTUP_TIMEOUT = 30
SHUTDOWN_TIMEOUT = 15

# --- 顏色代碼 ---
class colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_step(message): print(f"\n{colors.BOLD}>> {message}{colors.ENDC}")
def print_success(message): print(f"{colors.OKGREEN}✅ {message}{colors.ENDC}")
def print_error(message): print(f"{colors.FAIL}🔴 {message}{colors.ENDC}")

def cleanup():
    print_step("執行清理...")
    if VENV_DIR.exists():
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    # 清理 `colab_run` 可能產生的日誌
    if (PROJECT_ROOT / "logs.sqlite").exists():
        (PROJECT_ROOT / "logs.sqlite").unlink()
    if (PROJECT_ROOT / "作戰日誌歸檔").exists():
        shutil.rmtree(PROJECT_ROOT / "作戰日誌歸檔", ignore_errors=True)

def setup_venv():
    print_step("建立虛擬環境並安裝依賴...")
    if sys.platform == "win32":
        python_exe = VENV_DIR / "Scripts" / "python.exe"
    else:
        python_exe = VENV_DIR / "bin" / "python"

    # 確保使用正確的工作目錄
    subprocess.run([sys.executable, "-m", "venv", str(VENV_DIR)], check=True, cwd=PROJECT_ROOT)
    subprocess.run([str(python_exe), "-m", "pip", "install", "-r", str(PROJECT_ROOT / "requirements" / "base.txt")], check=True, capture_output=True, text=True, cwd=PROJECT_ROOT)
    print_success("虛擬環境準備就緒。")
    return python_exe

def terminate_process_tree(pid):
    try:
        parent = psutil.Process(pid)
        children = parent.children(recursive=True)
        for child in children:
            child.terminate()
        gone, alive = psutil.wait_procs(children, timeout=3)
        for p in alive:
            p.kill()
        parent.terminate()
        parent.wait(timeout=5)
        print_success(f"進程樹 (PID: {pid}) 已成功終止。")
    except psutil.NoSuchProcess:
        print_success(f"進程 (PID: {pid}) 在終止前已自行退出。")
    except Exception as e:
        print_error(f"終止進程樹時出錯: {e}")

def main():
    server_process = None
    exit_code = 0
    try:
        cleanup()
        python_executable = setup_venv()

        print_step("啟動核心服務 `server_main.py`...")
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)

        server_process = subprocess.Popen(
            [str(python_executable), str(PROJECT_ROOT / "server_main.py")],
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )

        print_step(f"等待服務上線 (最多 {STARTUP_TIMEOUT} 秒)...")
        start_time = time.time()
        service_ready = False
        while time.time() - start_time < STARTUP_TIMEOUT:
            try:
                with httpx.Client() as client:
                    response = client.get(SERVICE_URL, timeout=5)
                if response.status_code == 200:
                    print_success(f"服務在 {time.time() - start_time:.2f} 秒內成功回應！")
                    service_ready = True
                    break
            except httpx.RequestError:
                time.sleep(1)

        if not service_ready:
            raise RuntimeError(f"服務在 {STARTUP_TIMEOUT} 秒內未能啟動。")

        print(f"\n{colors.OKGREEN}{'='*40}{colors.ENDC}")
        print(f"{colors.OKGREEN}🎉 核心服務驗證成功！ 🎉")
        print(f"{colors.OKGREEN}{'='*40}{colors.ENDC}")

    except Exception as e:
        print_error(f"\n💥 測試失敗: {e}")
        if server_process:
            print("--- 服務輸出 ---")
            for line in server_process.stdout:
                print(line.strip())
            print("-----------------")
        exit_code = 1
    finally:
        if server_process and server_process.poll() is None:
            print_step("正在關閉服務...")
            terminate_process_tree(server_process.pid)

        cleanup()

        if exit_code == 0:
            print_step("測試成功，腳本自我銷毀...")
            TEST_SCRIPT_PATH.unlink()

        sys.exit(exit_code)

if __name__ == "__main__":
    main()
