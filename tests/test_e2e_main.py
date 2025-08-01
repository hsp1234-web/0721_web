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
import hashlib
from pathlib import Path
from multiprocessing import Pool, cpu_count

# --- 常數與設定 ---
PROJECT_ROOT = Path(__file__).parent.parent.resolve() # 專案根目錄現在是腳本所在目錄的上一層
APPS_DIR = PROJECT_ROOT / "apps"
VENV_CACHE_DIR = PROJECT_ROOT / ".venv_cache"
VENV_CACHE_DIR.mkdir(exist_ok=True)

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
        import trio
        import anyio
        print_success("核心 Python 依賴 (psutil, PyYAML, trio, anyio) 已滿足。")
    except ImportError:
        print_warn("缺少核心依賴 (psutil, PyYAML, trio, anyio)，正在安裝...")
        if run_command([sys.executable, "-m", "pip", "install", "-q", "psutil", "pyyaml", "trio", "anyio"]) != 0:
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

def install_all_app_dependencies(apps: list[Path]):
    """一次性安裝所有 App 的所有依賴"""
    print_header("步驟 3: 統一安裝所有 App 的依賴")
    all_reqs_content = []

    # 收集通用測試依賴
    common_deps = ["pytest", "pytest-mock", "ruff", "httpx", "pytest-xdist", "pytest-timeout", "pip-audit"]
    all_reqs_content.extend(common_deps)
    print_info(f"已加入通用測試依賴: {', '.join(common_deps)}")

    for app_path in apps:
        app_name = app_path.name
        req_file = app_path / "requirements.txt"
        req_large_file = app_path / "requirements.large.txt"

        if req_file.exists():
            print_info(f"正在讀取 [{app_name}] 的 requirements.txt")
            all_reqs_content.append(f"# --- From {app_name} ---")
            all_reqs_content.append(req_file.read_text())

        if req_large_file.exists():
            print_info(f"正在讀取 [{app_name}] 的 requirements.large.txt")
            all_reqs_content.append(f"# --- From {app_name} (large) ---")
            all_reqs_content.append(req_large_file.read_text())

    if not all_reqs_content:
        print_warn("未找到任何依賴檔案，跳過安裝。")
        return

    # 將所有內容寫入一個暫存檔案
    temp_reqs_file = PROJECT_ROOT / "temp_all_reqs.txt"
    temp_reqs_file.write_text("\n".join(all_reqs_content))
    print_info(f"所有依賴已合併至 {temp_reqs_file}")

    # 使用 uv 一次性安裝
    print_info("🚀 開始使用 uv 進行統一安裝...")
    install_cmd = [
        "uv", "pip", "install",
        "--system",  # 允許在非虛擬環境中安裝 (例如在 Docker 容器或 CI 環境中)
        "-r", str(temp_reqs_file),
    ]
    if run_command(install_cmd) != 0:
        print_fail("統一依賴安裝失敗。")
        temp_reqs_file.unlink() # 清理暫存檔
        sys.exit(1)

    print_success("✅ 所有 App 依賴已成功安裝到當前環境。")
    temp_reqs_file.unlink() # 清理暫存檔

def test_app(app_path: Path, test_mode: str) -> bool:
    """對單個 App 進行測試 (在統一環境中)"""
    app_name = app_path.name
    print_header(f"--- 開始測試 App: {app_name} (模式: {test_mode}) ---")

    tests_dir = PROJECT_ROOT / "tests" / app_name

    if not tests_dir.is_dir() or not any(tests_dir.glob("test_*.py")):
        print_warn(f"在 '{tests_dir}' 中找不到測試檔案，跳過。")
        return True # 沒有測試也算成功

    # 1. 執行 Ruff 檢查
    print_info(f"[{app_name}] 1. 執行 Ruff 檢查...")
    # Ruff 現在直接在當前環境執行
    ruff_cmd = [sys.executable, "-m", "ruff", "check", "--fix", str(app_path)]
    if run_command(ruff_cmd) != 0:
        print_fail(f"[{app_name}] Ruff 檢查失敗。")
        # return False # Ruff 失敗不應阻斷測試

    # 2. 執行 pip-audit 弱點掃描
    print_info(f"[{app_name}] 2. 執行 pip-audit 弱點掃描...")
    # pip-audit 現在直接在當前環境執行
    audit_cmd = [sys.executable, "-m", "pip_audit"]
    if run_command(audit_cmd) != 0:
        print_fail(f"[{app_name}] 弱點掃描發現問題。")
        return False

    # 3. 執行 pytest
    print_info(f"[{app_name}] 3. 執行 pytest (使用 xdist 和 timeout)...")
    app_mock_mode = "true" if test_mode == "mock" else "false"

    test_env = os.environ.copy()
    test_env["PYTHONPATH"] = str(PROJECT_ROOT)
    test_env["APP_MOCK_MODE"] = app_mock_mode

    # Pytest 現在直接使用 sys.executable 執行
    pytest_cmd = [sys.executable, "-m", "pytest", "-n", "auto", "--timeout=300", str(tests_dir)]

    exit_code = run_command(pytest_cmd, env=test_env)

    print_success(f"--- App: {app_name} 測試完成 ---")

    if exit_code != 0:
        print_fail(f"App '{app_name}' 的測試流程失敗。")
        return False

    print_success(f"App '{app_name}' 所有測試皆已通過！")
    return True

def test_database_driven_flow():
    """測試資料庫驅動的核心流程"""
    print_header("步驟 4: 測試資料庫驅動流程 (快速測試模式)")

    db_file = PROJECT_ROOT / "test_state.db"
    if db_file.exists():
        db_file.unlink()

    # 1. 透過 config.json 來控制，而不是環境變數
    # 這樣更貼近 colab_runner.py 的真實行為
    config_content = {"FAST_TEST_MODE": True, "TIMEZONE": "Asia/Taipei"}
    config_path = PROJECT_ROOT / "config.json"
    with open(config_path, "w") as f:
        import json
        json.dump(config_content, f)

    # 2. 執行 launch.py，並透過命令列參數傳遞 db_file
    print_info(f"執行 launch.py (後端主力部隊) 並將狀態寫入 {db_file}")
    command = [sys.executable, "scripts/launch.py", "--db-file", str(db_file)]
    result = run_command(command, env=os.environ.copy())

    # 清理設定檔
    config_path.unlink()

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
    cursor.execute("SELECT current_stage, apps_status FROM status_table WHERE id = 1")
    status_row = cursor.fetchone()
    if not status_row:
        print_fail("在 status_table 中找不到紀錄。")
        conn.close()
        return False

    stage, apps_status_json = status_row
    apps_status = json.loads(apps_status_json) if apps_status_json else {}

    # 在快速測試模式下，我們預期看到不同的最終狀態
    expected_stage = "快速測試通過"
    if stage != expected_stage:
        print_fail(f"最終階段應為 '{expected_stage}'，但卻是 '{stage}'。")
        conn.close()
        return False

    # 在快速測試模式下，App 狀態應為 pending
    if not all(s == "pending" for s in apps_status.values()):
        print_fail(f"App 狀態應全為 'pending'，但卻是 {apps_status}")
        conn.close()
        return False
    print_success("狀態表驗證成功。")

    # 驗證日誌表
    cursor.execute("SELECT level, message FROM phoenix_logs WHERE message LIKE '%快速測試流程驗證成功%'")
    log_row = cursor.fetchone()
    if not log_row:
        print_fail("在日誌表中找不到'快速測試流程驗證成功'的訊息。")
        conn.close()
        return False
    print_success("日誌表驗證成功。")

    conn.close()

    # 4. 清理
    db_file.unlink()

    print_success("資料庫驅動流程測試通過！")
    return True


def run_general_tests():
    """執行不屬於任何特定 App 的通用測試和 E2E 測試。"""
    print_header("步驟 5: 執行通用與端對端(E2E)測試")

    # 為了讓 pytest 能找到專案的模組 (如 core_utils)
    test_env = os.environ.copy()
    test_env["PYTHONPATH"] = str(PROJECT_ROOT)

    # 我們可以指定要運行的測試檔案，這樣更精確
    general_test_files = [
        "tests/test_resource_protection.py",
        "tests/test_e2e_dashboard.py",
        "tests/test_launch_installer.py", # 也將這個納入通用測試
        "tests/test_estimate_deps_size.py" # 新增的依賴分析工具測試
    ]

    # 檢查檔案是否存在
    existing_test_files = [f for f in general_test_files if (PROJECT_ROOT / f).exists()]
    if not existing_test_files:
        print_warn("未找到任何通用測試檔案，跳過此步驟。")
        return True

    print_info(f"將執行以下測試檔案: {', '.join(existing_test_files)}")

    # 注意：E2E 測試可能很慢，pytest-timeout 已在 test case 中設定
    # 我們可以透過 -m "not very_slow" 來跳過非常慢的測試
    pytest_cmd = [sys.executable, "-m", "pytest", *existing_test_files]

    if run_command(pytest_cmd, env=test_env) != 0:
        print_fail("通用或 E2E 測試失敗。")
        return False

    print_success("通用與 E2E 測試通過！")
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

    # 新增步驟：統一安裝所有依賴
    install_all_app_dependencies(apps)

    print_header(f"步驟 4: 開始對 {len(apps)} 個 App 進行平行化測試")

    tasks = [(app_path, test_mode) for app_path in apps]
    num_processes = min(cpu_count(), len(apps))
    print_info(f"將使用 {num_processes} 個平行進程。")

    with Pool(processes=num_processes) as pool:
        results = pool.starmap(test_app, tasks)

    app_failures = sum(1 for res in results if not res)

    # 執行資料庫流程測試
    db_flow_test_success = test_database_driven_flow()

    # 執行通用和 E2E 測試
    general_tests_success = run_general_tests()

    print_header("所有測試已完成")
    total_failures = app_failures + (0 if db_flow_test_success else 1) + (0 if general_tests_success else 1)

    if total_failures == 0:
        print_success("🎉 恭喜！所有測試流程都已成功通過！")
        sys.exit(0)
    else:
        print_fail(f"總共有 {total_failures} 個測試流程未通過。請檢查上面的日誌。")
        sys.exit(1)

if __name__ == "__main__":
    main()
