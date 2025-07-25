import os
import sys
import subprocess
import time
import venv
import webbrowser
from pathlib import Path

# --- Configuration ---
VENV_DIR = ".venv"
REQUIREMENTS_FILE = "requirements.txt"
MAIN_APP_MODULE = "main:app"
HOST = "127.0.0.1"
PORT = 8000

# --- Helper Functions ---
def is_in_venv():
    """檢查目前是否在虛擬環境中。"""
    return sys.prefix != sys.base_prefix

def get_executable(name):
    """在虛擬環境中找到可執行檔的路徑。"""
    venv_bin = Path(sys.prefix) / "bin"
    return str(venv_bin / name)

def print_header(title):
    """打印一個帶有標題的標頭。"""
    print("\n" + "="*60)
    print(f"🚀 {title}")
    print("="*60)

def print_success(message):
    """打印成功訊息。"""
    print(f"✅ {message}")

def print_info(message):
    """打印資訊訊息。"""
    print(f"ℹ️  {message}")

def print_warning(message):
    """打印警告訊息。"""
    print(f"⚠️  {message}")

def print_error(message):
    """打印錯誤訊息。"""
    print(f"❌ {message}")
    sys.exit(1)

# --- Main Logic ---
def setup_environment():
    """
    設定虛擬環境並使用 uv 安裝依賴。
    """
    print_header("環境設定")

    if is_in_venv() and Path(sys.prefix).name == VENV_DIR:
        print_success(f"已經在目標虛擬環境中: {sys.prefix}")
    else:
        if not Path(VENV_DIR).exists():
            print_info(f"正在建立虛擬環境於 '{VENV_DIR}'...")
            venv.create(VENV_DIR, with_pip=True)
            print_success(f"虛擬環境已建立。")
        else:
            print_success(f"虛擬環境 '{VENV_DIR}' 已存在。")

        print_error(f"請先啟動虛擬環境後再執行此腳本：\nsource {VENV_DIR}/bin/activate")

    # 使用 uv 安裝/同步依賴
    try:
        print_info("正在使用 'uv' 同步依賴... (這在首次執行時可能需要一些時間)")
        uv_executable = get_executable("uv")
        # 檢查 uv 是否存在，如果不存在，則先安裝
        if not Path(uv_executable).exists():
             subprocess.run([get_executable("pip"), "install", "uv"], check=True, capture_output=True, text=True)
             print_success("已成功安裝 'uv'。")

        # 使用 uv pip sync
        cmd = [uv_executable, "pip", "sync", REQUIREMENTS_FILE]
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        if result.stdout:
            print_info("uv stdout:\n" + result.stdout)
        if result.stderr:
            print_info("uv stderr:\n" + result.stderr)
        print_success("依賴已成功同步。")
    except FileNotFoundError:
        print_error(f"找不到 '{REQUIREMENTS_FILE}'。請確保該檔案存在於目前目錄。")
    except subprocess.CalledProcessError as e:
        print_error(f"依賴安裝失敗！\n命令: {' '.join(e.cmd)}\n返回碼: {e.returncode}\n輸出:\n{e.stdout}\n{e.stderr}")

def launch_backend():
    """
    在背景啟動 FastAPI/Uvicorn 伺服器。
    """
    print_header("啟動後端服務")
    try:
        uvicorn_executable = get_executable("uvicorn")
        cmd = [
            uvicorn_executable,
            MAIN_APP_MODULE,
            "--host", HOST,
            "--port", str(PORT),
            "--reload"  # 在開發時很有用
        ]
        print_info(f"正在執行命令: {' '.join(cmd)}")

        # 在背景啟動 uvicorn
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print_success(f"後端服務已在背景啟動 (PID: {process.pid})。")
        return process
    except FileNotFoundError:
        print_error("'uvicorn' 未安裝或找不到。請檢查您的虛擬環境和 `requirements.txt`。")
    except Exception as e:
        print_error(f"啟動後端服務失敗: {e}")

def launch_frontend():
    """
    打開瀏覽器訪問前端頁面。
    """
    print_header("啟動前端介面")
    url = f"http://{HOST}:{PORT}"
    print_info(f"等待 3 秒以確保後端服務完全啟動...")
    time.sleep(3)

    # 檢查是否在 Colab 環境中
    if "COLAB_GPU" in os.environ:
        print_info("偵測到 Colab 環境。正在生成嵌入式 iFrame...")
        try:
            from google.colab import output
            with output.redirect_to_element("#colab-output"):
                output.serve_kernel_port_as_iframe(PORT, height=800)
            print_success("Colab iFrame 已成功嵌入。")
        except ImportError:
            print_warning("無法導入 google.colab 模組。請在瀏覽器中手動打開以下 URL:")
            print_info(f"👉 {url}")
        except Exception as e:
             print_warning(f"嵌入 Colab iFrame 失敗: {e}。請在瀏覽器中手動打開以下 URL:")
             print_info(f"👉 {url}")

    else:
        print_info(f"正在預設瀏覽器中打開: {url}")
        try:
            webbrowser.open(url)
            print_success("瀏覽器分頁已打開。")
        except Exception as e:
            print_warning(f"自動打開瀏覽器失敗: {e}。請手動複製以下連結並打開：")
            print_info(f"👉 {url}")


if __name__ == "__main__":
    try:
        setup_environment()
        backend_process = launch_backend()
        launch_frontend()

        print_header("系統運行中")
        print_info("後端服務正在背景運行。")
        print_info("您可以透過瀏覽器介面與系統互動。")
        print_info("若要停止服務，請在此終端按下 Ctrl+C。")

        # 保持主腳本運行，以便監控後端進程的輸出
        while True:
            # 我們可以選擇性地讀取和打印後端的輸出以進行調試
            # stdout_line = backend_process.stdout.readline().strip()
            # if stdout_line:
            #     print(f"[BACKEND]: {stdout_line}")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n")
        print_info("偵測到使用者中斷 (Ctrl+C)。正在關閉服務...")
    except Exception as e:
        print_error(f"發生未預期的錯誤: {e}")
    finally:
        if 'backend_process' in locals() and backend_process.poll() is None:
            backend_process.terminate()
            backend_process.wait()
            print_success("後端服務已成功終止。")
        print_success("系統已安全關閉。")
