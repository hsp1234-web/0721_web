# -*- coding: utf-8 -*-
"""
🚀 鳳凰之心：端對端測試執行器 (Phoenix Heart: E2E Test Runner) 🚀

這個腳本專門用於自動化執行所有微服務應用程式的端對端測試。
它實現了與 `phoenix_starter.py` 相同的混合式依賴載入策略，以確保
測試環境與生產啟動環境的一致性。

核心功能:
- 自動化測試流程: 自動發現應用、準備環境、執行測試。
- 混合式依賴管理: 在記憶體中建立虛擬環境，將大型依賴安裝到磁碟。
- 環境一致性: 使用與主啟動器相同的邏輯設定 PYTHONPATH。
- CI/CD 友好: 無 TUI 介面，透過返回碼和日誌輸出清晰地報告成功或失敗。

使用方法:
    python run_e2e_tests.py
"""
import asyncio
import subprocess
import sys
from pathlib import Path
import os
import shlex
import shutil

# --- 常數與設定 ---
PROJECT_ROOT = Path(__file__).parent.resolve()
APPS_DIR = PROJECT_ROOT / "apps"
VENV_ROOT = Path("/dev/shm/phoenix_venvs_test") if sys.platform == "linux" and Path("/dev/shm").exists() else PROJECT_ROOT / ".venvs_test"
LARGE_PACKAGES_DIR = PROJECT_ROOT / ".large_packages_test"

# --- 顏色代碼 ---
class colors:
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    print(f"\n{colors.BOLD}🚀 {message} 🚀{colors.ENDC}")

def print_success(message):
    print(f"{colors.OKGREEN}✅ {message}{colors.ENDC}")

def print_fail(message):
    print(f"{colors.FAIL}❌ {message}{colors.ENDC}")

def print_info(message):
    print(f"ℹ️ {message}")

class App:
    """代表一個微服務應用程式的測試目標"""
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.venv_path = VENV_ROOT / self.name
        self.large_packages_path = LARGE_PACKAGES_DIR / self.name

def discover_apps() -> list[App]:
    """從 apps 目錄中發現所有應用"""
    apps = []
    for app_path in APPS_DIR.iterdir():
        if app_path.is_dir():
            apps.append(App(app_path))
    return apps

async def run_command(command: str, cwd: Path, env: dict = None):
    """異步執行一個子進程命令並等待其完成"""
    print_info(f"執行中: {command}")

    current_env = os.environ.copy()
    if env:
        current_env.update(env)

    if sys.platform != "win32":
        args = shlex.split(command)
        process = await asyncio.create_subprocess_exec(
            *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=current_env
        )
    else:
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=cwd,
            env=current_env
        )

    stdout, stderr = await process.communicate()

    if process.returncode != 0:
        print_fail(f"命令執行失敗，返回碼: {process.returncode}")
        if stdout:
            print(stdout.decode('utf-8', errors='replace'))
        if stderr:
            print(stderr.decode('utf-8', errors='replace'))

    return process.returncode

async def prepare_app_environment(app: App):
    """為單個 App 準備測試環境"""
    print_header(f"準備應用 '{app.name}' 的測試環境")

    try:
        # 1. 建立虛擬環境
        print_info(f"虛擬環境位置: {app.venv_path}")
        venv_cmd = f"uv venv {shlex.quote(str(app.venv_path))} --seed"
        if await run_command(venv_cmd, cwd=PROJECT_ROOT) != 0: return False

        python_executable = app.venv_path / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')
        if not python_executable.exists():
            print_fail(f"在 '{app.venv_path}' 中找不到 Python 解譯器")
            return False

        # 2. 安裝通用測試依賴
        common_deps = "pytest pytest-mock ruff httpx"
        pip_cmd = f'uv pip install --python "{python_executable}" {common_deps}'
        if await run_command(pip_cmd, cwd=PROJECT_ROOT) != 0: return False

        # 3. 安裝 App 核心依賴
        reqs_file = app.path / "requirements.txt"
        if reqs_file.exists():
            pip_cmd = f'uv pip install --python "{python_executable}" -r "{reqs_file}"'
            if await run_command(pip_cmd, cwd=PROJECT_ROOT) != 0: return False

        # 4. 安裝大型依賴到磁碟
        large_reqs_file = app.path / "requirements.large.txt"
        if large_reqs_file.exists():
            print_info(f"安裝大型依賴至: {app.large_packages_path}")
            app.large_packages_path.mkdir(parents=True, exist_ok=True)
            pip_cmd = f'uv pip install --target "{app.large_packages_path}" -r "{large_reqs_file}"'
            if await run_command(pip_cmd, cwd=PROJECT_ROOT) != 0: return False

        print_success(f"'{app.name}' 的環境已就緒")
        return True

    except Exception as e:
        print_fail(f"準備 '{app.name}' 環境時發生錯誤: {e}")
        return False

async def run_tests_for_app(app: App):
    """在 App 的虛擬環境中執行 pytest"""
    print_header(f"執行應用 '{app.name}' 的測試")

    tests_dir = app.path / "tests"
    if not tests_dir.exists() or not any(tests_dir.glob("test_*.py")):
        print_info("找不到測試檔案，跳過測試。")
        return True # 沒有測試也算通過

    python_executable = app.venv_path / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')

    # 設定環境變數
    env = {}
    python_path_parts = [str(PROJECT_ROOT)]
    if app.large_packages_path.exists():
        python_path_parts.append(str(app.large_packages_path))

    lib_path = app.venv_path / "lib"
    if lib_path.exists():
        py_version_dirs = list(lib_path.glob("python*"))
        if py_version_dirs:
            site_packages_path = py_version_dirs[0] / "site-packages"
            if site_packages_path.exists():
                python_path_parts.append(str(site_packages_path))

    env['PYTHONPATH'] = os.pathsep.join(python_path_parts)
    print_info(f"使用 PYTHONPATH: {env['PYTHONPATH']}")

    test_cmd = f'uv run --python "{python_executable}" pytest "{tests_dir}"'

    return_code = await run_command(test_cmd, cwd=PROJECT_ROOT, env=env)

    if return_code == 0:
        print_success(f"'{app.name}' 的所有測試均已通過！")
        return True
    else:
        print_fail(f"'{app.name}' 的測試失敗！")
        return False

def cleanup():
    """清理測試產生的暫存檔案"""
    print_header("清理測試環境")
    if VENV_ROOT.exists():
        print_info(f"正在刪除虛擬環境目錄: {VENV_ROOT}")
        shutil.rmtree(VENV_ROOT, ignore_errors=True)
    if LARGE_PACKAGES_DIR.exists():
        print_info(f"正在刪除大型依賴目錄: {LARGE_PACKAGES_DIR}")
        shutil.rmtree(LARGE_PACKAGES_DIR, ignore_errors=True)
    print_success("清理完成")

async def main():
    """主函數"""
    try:
        subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_fail("核心工具 `uv` 未安裝或找不到。請先安裝 uv: `pip install uv`")
        sys.exit(1)

    apps = discover_apps()
    if not apps:
        print_warning("在 'apps' 目錄下沒有找到任何應用。")
        sys.exit(0)

    print_info(f"發現 {len(apps)} 個應用: {[app.name for app in apps]}")

    # 清理舊的測試環境，確保乾淨的開始
    cleanup()

    VENV_ROOT.mkdir(exist_ok=True)
    LARGE_PACKAGES_DIR.mkdir(exist_ok=True)

    all_tests_passed = True
    for app in apps:
        env_ready = await prepare_app_environment(app)
        if not env_ready:
            all_tests_passed = False
            print_fail(f"因環境準備失敗，跳過 '{app.name}' 的測試。")
            continue

        tests_passed = await run_tests_for_app(app)
        if not tests_passed:
            all_tests_passed = False

    # 再次執行清理
    cleanup()

    if all_tests_passed:
        print_success("\n🎉 恭喜！所有應用的所有測試均已成功通過！ 🎉")
        sys.exit(0)
    else:
        print_fail("\n🔥 部分測試失敗。請檢查上面的日誌輸出。 🔥")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print_fail("\n測試被使用者中斷。")
        cleanup()
        sys.exit(1)
