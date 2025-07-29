# -*- coding: utf-8 -*-
"""
🚀 鳳凰之心：新一代智能測試指揮官 (Python Edition) 🚀

本腳本是 `smart_e2e_test.sh` 的 Python 現代化重構版本，旨在解決以下問題：
- 跨平台兼容性：在 Windows, macOS, Linux 和 Google Colab 上提供一致的體驗。
- 可維護性：使用 Python 讓邏輯更清晰，更易於擴展。
- 平行化基礎：為後續使用 `multiprocessing` 實現並行測試打下堅實基礎。

核心邏輯與 shell 版本保持一致：
- 絕對隔離：為每個 App 建立並銷毀獨立的測試虛擬環境。
- 模式切換：透過 `TEST_MODE` 環境變數支持 `mock` 和 `real` 模式。
- 資源感知：保留了對核心工具和資源的檢查。
"""

import os
import subprocess
import sys
import shutil
from pathlib import Path
from multiprocessing import Pool, cpu_count

# --- 常數與設定 ---
PROJECT_ROOT = Path(__file__).parent.resolve()
APPS_DIR = PROJECT_ROOT / "apps"

# --- 顏色代碼 ---
class C:
    HEADER = "\033[95m"
    CYAN = "\033[96m"
    GREEN = "\033[92m"
    WARN = "\033[93m"
    FAIL = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"

# --- 輔助函式 ---
def print_header(msg: str):
    print(f"\n{C.HEADER}{C.BOLD}🚀 {msg} 🚀{C.END}")

def print_success(msg: str):
    print(f"{C.GREEN}✅ {msg}{C.END}")

def print_info(msg: str):
    print(f"{C.CYAN}ℹ️ {msg}{C.END}")

def print_warn(msg: str):
    print(f"{C.WARN}⚠️ {msg}{C.END}")

def print_fail(msg: str):
    print(f"{C.FAIL}❌ {msg}{C.END}")

def run_command(command: list[str], cwd: Path = PROJECT_ROOT, env: dict = None) -> int:
    """執行一個子進程命令，並即時串流其輸出"""
    print_info(f"執行命令: {' '.join(command)}")
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        cwd=cwd,
        env=env or os.environ,
        text=True,
        encoding='utf-8',
        errors='replace'
    )
    while True:
        output = process.stdout.readline()
        if output == '' and process.poll() is not None:
            break
        if output:
            print(f"   {output.strip()}")
    return process.poll()

def check_core_tools():
    """檢查並確保 uv 和核心 Python 依賴已安裝"""
    print_header("步驟 1: 檢查核心工具")
    try:
        run_command(["uv", "--version"])
        print_success("uv 已就緒。")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print_warn("uv 未找到，正在安裝...")
        if run_command([sys.executable, "-m", "pip", "install", "-q", "uv"]) != 0:
            print_fail("安裝 uv 失敗。")
            sys.exit(1)
        print_success("uv 安裝成功。")

    try:
        import psutil
        import yaml
        print_success("核心 Python 依賴 (psutil, PyYAML) 已滿足。")
    except ImportError:
        print_warn("缺少核心依賴 (psutil, PyYAML)，正在安裝...")
        if run_command([sys.executable, "-m", "pip", "install", "-q", "psutil", "pyyaml"]) != 0:
            print_fail("安裝核心依賴失敗。")
            sys.exit(1)
        print_success("核心依賴安裝成功。")

def discover_apps() -> list[Path]:
    """從 apps 目錄中發現所有應用"""
    print_header("步驟 2: 發現 `apps` 目錄下的所有微服務")
    if not APPS_DIR.is_dir():
        print_fail(f"找不到 'apps' 目錄: {APPS_DIR}")
        return []
    apps = [d for d in APPS_DIR.iterdir() if d.is_dir()]
    print_info(f"發現了 {len(apps)} 個 App: {[app.name for app in apps]}")
    return apps

def test_app(app_path: Path, test_mode: str) -> bool:
    """對單個 App 進行隔離化測試"""
    app_name = app_path.name
    print_header(f"--- 開始測試 App: {app_name} (模式: {test_mode}) ---")

    venv_dir = app_path / ".venv_test_py"
    reqs_file = app_path / "requirements.txt"
    reqs_large_file = app_path / "requirements.large.txt"
    tests_dir = PROJECT_ROOT / "tests" / app_name

    if not tests_dir.is_dir() or not any(tests_dir.glob("test_*.py")):
        print_warn(f"在 '{tests_dir}' 中找不到測試檔案，跳過。")
        return True # 沒有測試也算成功

    # 1. 建立隔離的測試虛擬環境
    print_info(f"[{app_name}] 1. 建立隔離的測試虛擬環境...")
    if venv_dir.exists():
        print_warn(f"發現舊的虛擬環境，正在刪除: {venv_dir}")
        shutil.rmtree(venv_dir)
    if run_command(["uv", "venv", str(venv_dir), "--seed"]) != 0:
        print_fail(f"[{app_name}] 建立虛擬環境失敗。")
        return False

    python_exec = str(venv_dir / "bin" / "python")

    # 2. 安裝通用測試依賴
    print_info(f"[{app_name}] 2. 安裝通用測試依賴 (pytest, xdist, timeout, etc.)...")
    common_deps = ["pytest", "pytest-mock", "ruff", "httpx", "pytest-xdist", "pytest-timeout"]
    if run_command(["uv", "pip", "install", "-p", python_exec, *common_deps]) != 0:
        print_fail(f"[{app_name}] 安裝通用依賴失敗。")
        return False

    # 3. 啟動智慧型安全安裝程序
    print_info(f"[{app_name}] 3. 啟動智慧型安全安裝程序...")
    safe_installer_cmd = [
        sys.executable,
        "-m", "core_utils.safe_installer",
        app_name,
        str(reqs_file),
        python_exec
    ]
    # 需要先安裝核心依賴到虛擬環境中
    run_command(["uv", "pip", "install", "-p", python_exec, "pyyaml", "psutil"])
    if run_command(safe_installer_cmd) != 0:
        print_fail(f"[{app_name}] 安全安裝核心依賴失敗。")
        return False

    # 4. 根據測試模式決定是否安裝大型依賴
    app_mock_mode = "true"
    if test_mode == "real":
        app_mock_mode = "false"
        if reqs_large_file.exists():
            print_warn(f"[{app_name}] 偵測到真實模式，準備安全安裝大型依賴...")
            large_installer_cmd = [
                sys.executable,
                "-m", "core_utils.safe_installer",
                f"{app_name}_large",
                str(reqs_large_file),
                python_exec
            ]
            if run_command(large_installer_cmd) != 0:
                print_fail(f"[{app_name}] 安全安裝大型依賴失敗。")
                return False
            print_success(f"[{app_name}] 大型依賴安裝完成。")
    else:
        print_info(f"[{app_name}] 處於模擬模式，跳過大型依賴。")

    # 5. 執行 Ruff 檢查
    print_info(f"[{app_name}] 4. 執行 Ruff 檢查...")
    ruff_cmd = ["uv", "run", "-p", python_exec, "--", "ruff", "check", "--fix", str(app_path)]
    if run_command(ruff_cmd) != 0:
        print_fail(f"[{app_name}] Ruff 檢查失敗。")
        # return False # Ruff 失敗不應阻斷測試

    # 6. 執行 pytest
    print_info(f"[{app_name}] 5. 執行 pytest (使用 xdist 和 timeout)...")
    test_env = os.environ.copy()
    test_env["PYTHONPATH"] = str(PROJECT_ROOT)
    test_env["APP_MOCK_MODE"] = app_mock_mode
    pytest_cmd = ["uv", "run", "-p", python_exec, "--", "pytest", "-n", "auto", "--timeout=300", str(tests_dir)]

    exit_code = run_command(pytest_cmd, env=test_env)

    # 7. 清理
    print_info(f"清理 {app_name} 的測試環境...")
    shutil.rmtree(venv_dir)
    print_success(f"--- App: {app_name} 測試完成 ---")

    if exit_code != 0:
        print_fail(f"App '{app_name}' 的測試流程失敗。")
        return False

    print_success(f"App '{app_name}' 所有測試皆已通過！")
    return True

def test_database_driven_flow():
    """測試資料庫驅動的核心流程"""
    print_header("步驟 4: 測試資料庫驅動流程")

    db_file = PROJECT_ROOT / "test_state.db"
    if db_file.exists():
        db_file.unlink()

    # 1. 設置環境變數
    test_env = os.environ.copy()
    test_env["FAST_TEST_MODE"] = "true"
    test_env["DB_FILE"] = str(db_file)

    # 2. 執行 launch.py (後端主力部隊)
    print_info("執行 launch.py (後端主力部隊)...")
    result = run_command([sys.executable, "launch.py"], env=test_env)

    if result != 0:
        print_fail("launch.py 執行失敗。")
        return False

    # 3. 驗證資料庫是否生成且內容正確
    if not db_file.exists():
        print_fail(f"資料庫檔案未找到: {db_file}")
        return False

    import sqlite3
    import json
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # 驗證狀態表
    cursor.execute("SELECT current_stage, apps_status, action_url FROM status_table WHERE id = 1")
    status_row = cursor.fetchone()
    if not status_row:
        print_fail("在 status_table 中找不到紀錄。")
        return False

    stage, apps_status_json, action_url = status_row
    apps_status = json.loads(apps_status_json)

    if stage != "completed":
        print_fail(f"最終階段應為 'completed'，但卻是 '{stage}'。")
        return False
    if not all(s == "running" for s in apps_status.values()):
        print_fail(f"並非所有 App 狀態皆為 'running': {apps_status}")
        return False
    if action_url != "http://localhost:8000/dashboard":
        print_fail(f"action_url 不正確: {action_url}")
        return False
    print_success("狀態表驗證成功。")

    # 驗證日誌表
    cursor.execute("SELECT level, message FROM log_table WHERE message LIKE '%所有服務已成功啟動%'")
    log_row = cursor.fetchone()
    if not log_row:
        print_fail("在日誌表中找不到成功啟動的訊息。")
        return False
    print_success("日誌表驗證成功。")

    conn.close()

    # 4. 清理
    db_file.unlink()

    print_success("資料庫驅動流程測試通過！")
    return True


def main():
    """主函數"""
    test_mode = os.environ.get("TEST_MODE", "mock")
    print_header(f"鳳凰之心智能測試開始 (模式: {test_mode})")

    check_core_tools()
    apps = discover_apps()

    if not apps:
        print_warn("未發現任何 App，測試結束。")
        sys.exit(0)

    print_header(f"步驟 3: 開始對 {len(apps)} 個 App 進行平行化測試")

    tasks = [(app_path, test_mode) for app_path in apps]
    num_processes = min(cpu_count(), len(apps))
    print_info(f"將使用 {num_processes} 個平行進程。")

    with Pool(processes=num_processes) as pool:
        results = pool.starmap(test_app, tasks)

    app_failures = sum(1 for res in results if not res)

    # 執行資料庫流程測試
    db_flow_test_success = test_database_driven_flow()

    print_header("所有測試已完成")
    if app_failures == 0 and db_flow_test_success:
        print_success("🎉 恭喜！所有 App 的測試都已成功通過！")
        sys.exit(0)
    else:
        total_failures = app_failures + (0 if db_flow_test_success else 1)
        print_fail(f"總共有 {total_failures} 個測試流程未通過。請檢查上面的日誌。")
        sys.exit(1)

if __name__ == "__main__":
    main()
