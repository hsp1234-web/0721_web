# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 鳳凰之心 Colab 整合啟動器 v2 (全功能版)                         ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   v2 更新：                                                          ║
# ║       - 整合 Git 下載：將從 GitHub 拉取程式碼的邏輯內建。            ║
# ║       - 完整參數化：保留了所有 v14 範本中的參數，包括 Git 設定、     ║
# ║         日誌、時區等，使其成為一個完整的「從零到一」啟動腳本。       ║
# ║       - 流程最佳化：將下載、環境準備、應用啟動流程化，更穩健。       ║
# ║                                                                      ║
# ║   使用方式：                                                         ║
# ║       1. 將此檔案的全部內容複製到一個 Google Colab 儲存格中。        ║
# ║       2. 根據您的需求修改下面的參數區塊。                            ║
# ║       3. 執行該儲存格。                                              ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# ==============================================================================
# 參數設定區 (Colab Form)
# ==============================================================================
#@title 💎 鳳凰之心指揮中心 (全功能 Colab 版) { vertical-output: true, display-mode: "form" }

#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
TARGET_BRANCH_OR_TAG = "main" #@param {type:"string"}
PROJECT_FOLDER_NAME = "phoenix_project" #@param {type:"string"}
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 應用程式與安裝參數**
#@markdown > **設定安裝模式與各個微服務的核心參數。**
#@markdown ---
INSTALL_MODE = "模擬安裝 (僅核心依賴)" #@param ["完整安裝 (包含大型依賴)", "模擬安裝 (僅核心依賴)"]
QUANT_APP_PORT = 8001 #@param {type:"integer"}
TRANSCRIBER_APP_PORT = 8002 #@param {type:"integer"}

#@markdown ---
#@markdown ### **Part 3: 指揮中心運行參數**
#@markdown > **這些參數主要用於 TUI 或其他監控工具，此處保留以便未來擴展。**
#@markdown ---
REFRESH_RATE_SECONDS = 5 #@param {type:"number"}
LOG_DISPLAY_LINES = 20 #@param {type:"integer"}
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
TIMEZONE = "Asia/Taipei" #@param {type:"string"}

# ==============================================================================
# 核心啟動邏輯
# ==============================================================================
import os
import sys
import subprocess
import shlex
import shutil
from pathlib import Path
import time

# --- 顏色代碼 ---
class colors:
    HEADER = '\033[95m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

# --- 輔助函數 ---
def print_header(message): print(f"\n{colors.HEADER}{colors.BOLD}🚀 {message} 🚀{colors.ENDC}")
def print_success(message): print(f"{colors.OKGREEN}✅ {message}{colors.ENDC}")
def print_warning(message): print(f"{colors.WARNING}⚠️ {message}{colors.ENDC}")
def print_info(message): print(f"ℹ️ {message}")

def run_command(command: str, cwd: Path, env: dict = None):
    print_info(f"執行中: {colors.BOLD}{command}{colors.ENDC}")
    current_env = os.environ.copy()
    if env: current_env.update(env)
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
        if output == '' and process.poll() is not None: break
        if output: print(f"   {output.strip()}")
    return process.wait()

# --- 主要功能函數 ---
def setup_project_code(base_path: Path, project_path: Path):
    """下載或更新專案程式碼"""
    print_header("步驟 1/4: 準備專案程式碼")
    if FORCE_REPO_REFRESH and project_path.exists():
        print_warning(f"偵測到「強制刷新」，正在刪除舊資料夾: {project_path}")
        shutil.rmtree(project_path)
        print_success("舊資料夾已移除。")

    if not project_path.exists():
        print_info(f"開始從 GitHub (分支/標籤: {TARGET_BRANCH_OR_TAG}) 拉取程式碼...")
        git_command = f"git clone -q --branch {TARGET_BRANCH_OR_TAG} --depth 1 {REPOSITORY_URL} {project_path.name}"
        if run_command(git_command, cwd=base_path) != 0:
            print(f"{colors.FAIL}Git clone 失敗！請檢查 URL 和分支名稱。{colors.ENDC}")
            return False
        print_success("程式碼成功下載！")
    else:
        print_success(f"資料夾 '{project_path.name}' 已存在，跳過下載。")
    return True

def prepare_environments(project_path: Path):
    """準備所有 App 的混合式依賴環境"""
    print_header("步驟 2/4: 準備依賴環境 (混合式)")

    # 定義路徑
    apps_dir = project_path / "apps"
    venv_root = Path(f"/dev/shm/{PROJECT_FOLDER_NAME}_venvs") if sys.platform == "linux" else project_path / ".venvs"
    large_packages_dir = project_path / ".large_packages"
    install_large_deps = "完整安裝" in INSTALL_MODE

    # 確保 uv 已安裝
    print_info("檢查核心工具 uv...")
    try:
        subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("uv 未找到，正在從 pip 安裝...")
        if subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True).returncode != 0:
            print(f"{colors.FAIL}uv 安裝失敗！{colors.ENDC}")
            return False

    # 清理並建立根目錄
    if venv_root.exists(): shutil.rmtree(venv_root)
    if large_packages_dir.exists(): shutil.rmtree(large_packages_dir)
    venv_root.mkdir(parents=True, exist_ok=True)
    if install_large_deps: large_packages_dir.mkdir(parents=True, exist_ok=True)

    print_info(f"虛擬環境根目錄: {venv_root}")
    if install_large_deps: print_info(f"大型依賴目錄: {large_packages_dir}")

    apps_to_prepare = [d for d in apps_dir.iterdir() if d.is_dir()]
    for app_path in apps_to_prepare:
        app_name = app_path.name
        print_info(f"--- 正在準備 App: {app_name} ---")
        venv_path = venv_root / app_name
        python_executable = venv_path / 'bin/python'

        if run_command(f"uv venv '{venv_path}' --seed", cwd=project_path) != 0: return False

        reqs_path = app_path / "requirements.txt"
        if reqs_path.exists():
            if run_command(f"uv pip install --python '{python_executable}' -r '{reqs_path}'", cwd=project_path) != 0: return False

        large_reqs_path = app_path / "requirements.large.txt"
        if install_large_deps and large_reqs_path.exists():
            target_dir = large_packages_dir / app_name
            target_dir.mkdir(exist_ok=True)
            if run_command(f"uv pip install --target '{target_dir}' -r '{large_reqs_path}'", cwd=project_path) != 0: return False

    print_success("所有 App 環境均已準備就緒！")
    return True

def launch_apps(project_path: Path):
    """啟動所有應用程式"""
    print_header("步驟 3/4: 啟動所有應用程式")

    apps_dir = project_path / "apps"
    venv_root = Path(f"/dev/shm/{PROJECT_FOLDER_NAME}_venvs") if sys.platform == "linux" else project_path / ".venvs"
    large_packages_dir = project_path / ".large_packages"
    install_large_deps = "完整安裝" in INSTALL_MODE

    app_ports = {"quant": QUANT_APP_PORT, "transcriber": TRANSCRIBER_APP_PORT}
    processes = []

    for app_path in (d for d in apps_dir.iterdir() if d.is_dir()):
        app_name = app_path.name
        port = app_ports.get(app_name)
        if not port: continue

        print_info(f"--- 正在啟動 App: {app_name} (埠號: {port}) ---")
        venv_path = venv_root / app_name
        venv_python = venv_path / 'bin/python'
        main_py_path = app_path / "main.py"

        env = os.environ.copy()
        python_path_parts = [str(project_path)]

        if install_large_deps:
            app_large_pkg_path = large_packages_dir / app_name
            if app_large_pkg_path.exists():
                python_path_parts.append(str(app_large_pkg_path))

        py_version_dir = next((venv_path / "lib").glob("python*"), None)
        if py_version_dir and (py_version_dir / "site-packages").exists():
            python_path_parts.append(str(py_version_dir / "site-packages"))

        env["PYTHONPATH"] = os.pathsep.join(python_path_parts)
        env["PORT"] = str(port)
        env["TIMEZONE"] = TIMEZONE

        print_info(f"使用 PYTHONPATH: {env['PYTHONPATH']}")

        log_file = Path(f"/content/{app_name}.log")
        print_info(f"日誌將輸出到: {log_file}")

        process = subprocess.Popen(
            [str(venv_python), str(main_py_path)],
            env=env,
            stdout=log_file.open('w'),
            stderr=subprocess.STDOUT
        )
        processes.append(process)
        print_success(f"App '{app_name}' 已在背景啟動，PID: {process.pid}")

    return processes

def final_summary(processes, start_time):
    """顯示最終的總結資訊"""
    print_header("步驟 4/4: 系統狀態總結")
    end_time = time.time()
    print(f"{colors.OKGREEN}{colors.BOLD}✅ 鳳凰之心系統已成功啟動！ (總耗時: {end_time - start_time:.2f} 秒){colors.ENDC}")
    print("="*60)
    print("各服務正在背景運行中。PIDs:", ", ".join(str(p.pid) for p in processes))
    print(f"  - Quant 服務應監聽於埠: {QUANT_APP_PORT}")
    print(f"  - Transcriber 服務應監聽於埠: {TRANSCRIBER_APP_PORT}")
    print(f"\n日誌檔案位於 /content/quant.log 和 /content/transcriber.log")
    print("您現在可以使用 `ngrok` 等工具將服務暴露到公網，或在 Colab 中直接與之互動。")
    print("\n若要停止所有服務，請中斷或重新啟動 Colab 執行階段。")

def main():
    """主協調函式"""
    start_time = time.time()

    try:
        from IPython.display import clear_output
        clear_output(wait=True)
    except ImportError:
        pass

    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    if not setup_project_code(base_path, project_path): return

    # 關鍵：切換工作目錄到專案根目錄
    os.chdir(project_path)
    print_success(f"工作目錄已切換至: {os.getcwd()}")

    if not prepare_environments(project_path): return

    processes = launch_apps(project_path)
    if not processes:
        print(f"\n{colors.FAIL}❌ 未能啟動任何應用程式，啟動中止。{colors.ENDC}")
        return

    final_summary(processes, start_time)

    # 保持腳本運行以監控進程
    try:
        while True:
            time.sleep(300) # 每 5 分鐘檢查一次
            for p in processes:
                if p.poll() is not None:
                    print_warning(f"警告：偵測到進程 PID {p.pid} 已終止。")
    except KeyboardInterrupt:
        print(f"\n{colors.WARNING}收到手動中斷信號，正在關閉所有服務...{colors.ENDC}")
        for p in processes: p.terminate()
        for p in processes: p.wait()
        print_success("所有服務已成功關閉。")

if __name__ == "__main__":
    main()
