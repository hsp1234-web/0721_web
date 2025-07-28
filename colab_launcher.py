# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 鳳凰之心 Colab 整合啟動器                                       ║
# ║   (Phoenix Heart: Colab Integrated Launcher)                         ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       - 單一腳本：將所有啟動邏輯整合到一個檔案中，方便複製貼上。     ║
# ║       - Colab 優先：專為在 Google Colab 環境中執行而設計。           ║
# ║       - 混合式載入：保留高效的混合式依賴策略，在 Colab 的 Linux      ║
# ║         環境下利用記憶體檔案系統 (`/dev/shm`) 以提升效能。           ║
# ║       - 職責單一：此腳本專注於「啟動應用」，不包含測試或代理邏輯。     ║
# ║                                                                      ║
# ║   使用方式：                                                         ║
# ║       1. 將此檔案的全部內容複製到一個 Google Colab 儲存格中。        ║
# ║       2. 根據您的需求修改下面的參數區塊。                            ║
# ║       3. 執行該儲存格。                                              ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# ==============================================================================
# 參數設定區 (模仿 Colab 表單)
# ==============================================================================
#@title 💎 鳳凰之心 Colab 啟動器 { vertical-output: true, display-mode: "form" }

# --- 安裝模式 ---
#@markdown > **決定是否安裝大型依賴包 (例如 AI 模型)。在資源有限的 Colab 環境中，建議選擇 '模擬安裝'。**
INSTALL_MODE = "模擬安裝 (僅核心依賴)" #@param ["完整安裝 (包含大型依賴)", "模擬安裝 (僅核心依賴)"]

# --- 埠號設定 ---
#@markdown > **為每個微服務應用指定啟動的埠號。**
QUANT_APP_PORT = 8001 #@param {type:"integer"}
TRANSCRIBER_APP_PORT = 8002 #@param {type:"integer"}

# ==============================================================================
# 核心啟動邏輯
# ==============================================================================
import os
import sys
import subprocess
import shlex
from pathlib import Path
import time

# --- 常數與設定 ---
PROJECT_ROOT = Path(os.getcwd())
APPS_DIR = PROJECT_ROOT / "apps"
# 在 Colab (Linux) 的 /dev/shm/ 或本地的 .venvs_colab 目錄下建立虛擬環境
VENV_ROOT = Path("/dev/shm/phoenix_venvs_colab") if sys.platform == "linux" and Path("/dev/shm").exists() else PROJECT_ROOT / ".venvs_colab"
LARGE_PACKAGES_DIR = PROJECT_ROOT / ".large_packages_colab"
INSTALL_LARGE_DEPS = "完整安裝" in INSTALL_MODE

# --- 顏色代碼 ---
class colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# --- 輔助函數 ---
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

def run_command(command: str, cwd: Path = PROJECT_ROOT, env: dict = None):
    """執行一個子進程命令，並即時串流其輸出"""
    print_info(f"執行中: {colors.BOLD}{command}{colors.ENDC}")

    current_env = os.environ.copy()
    if env:
        current_env.update(env)

    process = subprocess.Popen(
        shlex.split(command),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        text=True,
        encoding='utf-8',
        errors='replace',
        env=current_env
    )

    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"   {output.strip()}")

    return process.wait()

# --- 核心功能函數 ---
def prepare_all_environments():
    """準備所有 App 的環境和依賴"""
    print_header("環境準備階段")

    # 確保 uv 已安裝
    print_info("檢查核心工具 uv...")
    try:
        subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
        print_success("uv 已安裝。")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("uv 未找到，正在從 pip 安裝...")
        if run_command(f"{sys.executable} -m pip install -q uv") != 0:
            print(f"{colors.FAIL}uv 安裝失敗，請手動執行 `pip install uv`。{colors.ENDC}")
            return False

    # 清理並建立根目錄
    if VENV_ROOT.exists():
        print_info(f"清理舊的虛擬環境目錄: {VENV_ROOT}")
        run_command(f"rm -rf {VENV_ROOT}")
    if LARGE_PACKAGES_DIR.exists():
        print_info(f"清理舊的大型依賴目錄: {LARGE_PACKAGES_DIR}")
        run_command(f"rm -rf {LARGE_PACKAGES_DIR}")

    VENV_ROOT.mkdir(parents=True, exist_ok=True)
    if INSTALL_LARGE_DEPS:
        LARGE_PACKAGES_DIR.mkdir(parents=True, exist_ok=True)

    print_info(f"將在記憶體中建立虛擬環境: {VENV_ROOT}")
    if INSTALL_LARGE_DEPS:
        print_info(f"大型依賴將安裝至磁碟: {LARGE_PACKAGES_DIR}")
    else:
        print_warning("已選擇模擬安裝模式，將跳過大型依賴。")

    apps_to_prepare = [d for d in APPS_DIR.iterdir() if d.is_dir()]
    for app_path in apps_to_prepare:
        app_name = app_path.name
        print_header(f"正在準備 App: {app_name}")

        venv_path = VENV_ROOT / app_name
        large_packages_path = LARGE_PACKAGES_DIR / app_name
        requirements_path = app_path / "requirements.txt"
        large_requirements_path = app_path / "requirements.large.txt"

        # 1. 建立虛擬環境
        if run_command(f"uv venv '{venv_path}' --seed") != 0: return False
        python_executable = venv_path / 'bin/python'

        # 2. 安裝核心依賴
        if requirements_path.exists():
            if run_command(f"uv pip install --python '{python_executable}' -r '{requirements_path}'") != 0: return False

        # 3. 安裝大型依賴 (如果需要)
        if INSTALL_LARGE_DEPS and large_requirements_path.exists():
            if run_command(f"uv pip install --target '{large_packages_path}' -r '{large_requirements_path}'") != 0: return False

    print_success("所有 App 環境均已準備就緒！")
    return True

def launch_all_apps():
    """在背景啟動所有 App"""
    print_header("應用啟動階段")

    app_ports = {
        "quant": QUANT_APP_PORT,
        "transcriber": TRANSCRIBER_APP_PORT
    }

    apps_to_launch = [d for d in APPS_DIR.iterdir() if d.is_dir()]
    processes = []

    for app_path in apps_to_launch:
        app_name = app_path.name
        port = app_ports.get(app_name)
        if not port:
            print_warning(f"未找到應用 '{app_name}' 的埠號設定，跳過啟動。")
            continue

        print_header(f"正在啟動 App: {app_name} (埠號: {port})")

        venv_path = VENV_ROOT / app_name
        large_packages_path = LARGE_PACKAGES_DIR / app_name
        venv_python = venv_path / 'bin/python'
        main_py_path = app_path / "main.py"

        # 設定 PYTHONPATH
        env = os.environ.copy()
        python_path_parts = [str(PROJECT_ROOT)]
        if INSTALL_LARGE_DEPS and large_packages_path.exists():
            python_path_parts.append(str(large_packages_path))

        lib_path = venv_path / "lib"
        py_version_dir = next(lib_path.glob("python*"), None)
        if py_version_dir:
            site_packages_path = py_version_dir / "site-packages"
            if site_packages_path.exists():
                python_path_parts.append(str(site_packages_path))

        env["PYTHONPATH"] = os.pathsep.join(python_path_parts)
        env["PORT"] = str(port) # 讓應用內部可以讀取

        print_info(f"使用 PYTHONPATH: {env['PYTHONPATH']}")

        # 在背景啟動進程
        process = subprocess.Popen(
            [str(venv_python), str(main_py_path)],
            env=env
        )
        processes.append(process)
        print_success(f"App '{app_name}' 已在背景啟動，PID: {process.pid}")

    return processes

# --- 主執行流程 ---
def main():
    """主協調函式"""
    start_time = time.time()

    # 步驟 1: 準備環境
    if not prepare_all_environments():
        print(f"\n{colors.FAIL}❌ 環境準備失敗，啟動中止。{colors.ENDC}")
        return

    # 步驟 2: 啟動應用
    processes = launch_all_apps()
    if not processes:
        print(f"\n{colors.FAIL}❌ 未能啟動任何應用程式，啟動中止。{colors.ENDC}")
        return

    end_time = time.time()
    print("\n" + "="*60)
    print(f"{colors.OKGREEN}{colors.BOLD}✅ 鳳凰之心系統已成功啟動！ (總耗時: {end_time - start_time:.2f} 秒){colors.ENDC}")
    print("="*60)
    print("各服務正在背景運行中。您現在可以：")
    print(f"  - Quant 服務監聽於埠: {QUANT_APP_PORT}")
    print(f"  - Transcriber 服務監聽於埠: {TRANSCRIBER_APP_PORT}")
    print("\n在 Colab 中，您可能需要使用 `ngrok` 或類似工具將這些埠暴露給公網。")
    print("若要停止所有服務，請中斷或重新啟動 Colab 執行階段。")

    # 讓腳本保持運行，以維持背景進程
    try:
        while True:
            time.sleep(60)
            print(f"\n{colors.OKBLUE}[{time.strftime('%Y-%m-%d %H:%M:%S')}] 系統運行中... PIDs: {[p.pid for p in processes]}{colors.ENDC}")
    except KeyboardInterrupt:
        print(f"\n{colors.WARNING}收到手動中斷信號，正在關閉所有服務...{colors.ENDC}")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print_f"{colors.OKGREEN}所有服務已成功關閉。{colors.ENDC}"

if __name__ == "__main__":
    # 確保我們在正確的目錄下
    # 在 Colab 中，這通常是 /content/YOUR_PROJECT_FOLDER
    # 這段程式碼假設您已經手動或透過 git clone 將專案放在了當前工作目錄
    if not APPS_DIR.exists():
        print(f"{colors.FAIL}錯誤：找不到 'apps' 資料夾。{colors.ENDC}")
        print(f"請確保您已經將專案程式碼下載到當前目錄，並且此腳本是從專案根目錄執行的。")
        print(f"當前工作目錄: {os.getcwd()}")
    else:
        main()
