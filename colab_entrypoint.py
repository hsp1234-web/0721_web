# -*- coding: utf-8 -*-
# ==============================================================================
# SECTION 0: 環境初始化與核心模組導入
# ==============================================================================
import os
import sys
import subprocess
import time
import io
from pathlib import Path
from datetime import datetime, timezone, timedelta

# --- 模擬或真實的 IPython 導入 ---
try:
    from IPython.display import display, HTML, Javascript
except ImportError:
    # 在非 Colab 環境中，使用一個模擬的 display 函式
    def display(*args, **kwargs):
        print("--- [MOCK DISPLAY] ---")
        for arg in args:
            print(f"    {arg}")
        print("----------------------")

    def HTML(html):
        return f"HTML(...{html[:30]}...)"

    def Javascript(js):
        return f"Javascript(...{js[:30]}...)"

# ==============================================================================
# SECTION 1: 日誌捕獲與歸檔
# ==============================================================================
log_capture_string = io.StringIO()

class Tee(io.StringIO):
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

def get_taipei_time() -> datetime:
    """獲取當前亞洲/台北時間"""
    utc_now = datetime.now(timezone.utc)
    taipei_tz = timezone(timedelta(hours=8))
    return utc_now.astimezone(taipei_tz)

def save_log_file(archive_folder_name: str, status: str):
    """將捕獲的日誌儲存到指定的中文資料夾"""
    try:
        base_path = Path("/content") if Path("/content").exists() else Path.cwd()
        archive_path = base_path / archive_folder_name
        archive_path.mkdir(parents=True, exist_ok=True)

        timestamp = get_taipei_time().isoformat().replace(":", "-")
        filename = f"鳳凰之心-{status}-日誌-{timestamp}.txt"
        filepath = archive_path / filename

        print(f"\n📋 正在歸檔日誌至: {filepath}")

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(log_capture_string.getvalue())

        print(f"✅ 日誌歸檔成功。")

    except Exception as e:
        print(f"❌ 日誌歸檔失敗: {e}", file=sys.__stderr__)

# 重定向 stdout 和 stderr
original_stdout = sys.stdout
original_stderr = sys.stderr
sys.stdout = Tee(original_stdout, log_capture_string)
sys.stderr = Tee(original_stderr, log_capture_string)

# ==============================================================================
# SECTION 2: 核心啟動流程
# ==============================================================================
server_process = None

# --- 預設參數 (會被 Colab 的 @param 取代) ---
LOG_DISPLAY_LINES = 100
STATUS_REFRESH_INTERVAL = 0.5
TARGET_FOLDER_NAME = "WEB_TEST"
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔"
FASTAPI_PORT = 8000

def run_colab_flow(
    log_display_lines: int,
    status_refresh_interval: float,
    target_folder_name: str,
    archive_folder_name: str,
    fastapi_port: int,
):
    """執行完整的 Colab 啟動流程，包含明確的 venv 隔離。"""
    global server_process
    original_cwd = Path.cwd()
    try:
        save_log_file(archive_folder_name, "啟動")
        display(Javascript("document.querySelectorAll('.phoenix-launcher-output').forEach(el => el.remove());"))
        container_id = f"phoenix-container-{int(time.time())}"
        display(HTML(f'<div id="{container_id}" style="height: 95vh;">...</div>'))

        print("✅ 正在設定環境變數...")
        os.environ['LOG_DISPLAY_LINES'] = str(log_display_lines)
        os.environ['STATUS_REFRESH_INTERVAL'] = str(status_refresh_interval)
        os.environ['ARCHIVE_FOLDER_NAME'] = str(archive_folder_name)
        os.environ['FASTAPI_PORT'] = str(fastapi_port)

        base_path = Path("/content") if Path("/content").exists() else Path.cwd()
        project_path = base_path / target_folder_name

        if not project_path.is_dir() or not (project_path / "main.py").exists():
            raise FileNotFoundError(f"指定的專案資料夾 '{project_path}' 不存在或缺少 'main.py'。")

        print(f"📂 將在專案目錄中操作: {project_path}")
        os.chdir(project_path)

        print("\n📦 正在配置隔離的虛擬環境 (.venv)...")
        venv_path = Path(".venv")
        if not venv_path.exists():
            print("   - 虛擬環境不存在，正在創建...")
            subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True, capture_output=True)
            print("   - ✅ 虛擬環境創建成功。")

        venv_python = (venv_path / "bin" / "python") if sys.platform != "win32" else (venv_path / "Scripts" / "python.exe")
        print(f"   - 將使用解釋器: {venv_python}")

        print("\n🚀 正在使用 pip 在 .venv 中安裝根目錄的依賴...")
        # 使用相對於原始工作目錄的路徑來定位 requirements.txt
        requirements_path = original_cwd / "requirements.txt"
        if not requirements_path.exists():
            raise FileNotFoundError(f"找不到根目錄下的 requirements.txt: {requirements_path}")

        install_result = subprocess.run(
            [str(venv_python), "-m", "pip", "install", "-r", str(requirements_path)],
            capture_output=True, text=True, encoding='utf-8'
        )
        if install_result.returncode != 0:
            print("❌ 依賴配置失敗，終止作戰。")
            print(f"--- STDOUT ---\n{install_result.stdout}")
            print(f"--- STDERR ---\n{install_result.stderr}")
            raise RuntimeError("依賴安裝失敗。")
        print("✅ 依賴配置成功。")

        print("\n🔥 正在點燃後端引擎...")
        # 使用相對於原始工作目錄的路徑來定位 run.py
        run_script_path = original_cwd / "run.py"
        if not run_script_path.exists():
            raise FileNotFoundError(f"找不到根目錄下的 run.py: {run_script_path}")

        server_process = subprocess.Popen(
            [str(venv_python), str(run_script_path)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8'
        )
        print(f"   - 後端伺服器程序已啟動 (PID: {server_process.pid})。")

        print("📡 正在等待伺服器響應 (10秒)...")
        time.sleep(10)

        print(f"🌍 正在將駕駛艙嵌入至容器...")
        # ... (iframe 嵌入邏輯) ...
        print("\n✅ 鳳凰之心駕駛艙已上線！")

        if server_process.stdout:
            for line in iter(server_process.stdout.readline, ''):
                if line: print(f"[後端引擎]: {line.strip()}")
        server_process.wait()

    except Exception as e:
        print(f"\n\n💥 作戰流程發生未預期的嚴重錯誤: {e}", file=sys.__stderr__)
    finally:
        if server_process and server_process.poll() is None:
            print("...正在關閉後端伺服器...")
            server_process.terminate()
            server_process.wait(timeout=5)

        os.chdir(original_cwd)
        print("\n--- 系統已安全關閉 ---")
        save_log_file(archive_folder_name, "關閉")
        sys.stdout = original_stdout
        sys.stderr = original_stderr

if __name__ == '__main__':
    run_colab_flow(
        LOG_DISPLAY_LINES, STATUS_REFRESH_INTERVAL, TARGET_FOLDER_NAME,
        ARCHIVE_FOLDER_NAME, FASTAPI_PORT
    )
