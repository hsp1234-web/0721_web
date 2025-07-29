# -*- coding: utf-8 -*-
"""
鳳凰之心 - 隔離式自動化測試執行器 v1.0
(Phoenix Heart - Isolated Automated Test Runner v1.0)

本腳本為專案提供了最穩健的自動化測試方案，完全遵循了「服務級隔離測試」的核心理念。

核心邏輯:
1.  **發現 App**: 自動在 `src` 目錄下尋找所有可測試的微服務 App。
2.  **獨立環境**: 為每一個發現的 App，在 App 目錄內建立一個專用的虛擬環境 (`.venv_test`)。
3.  **隔離安裝**: 僅將該 App 自身需要的依賴 (`requirements/base.txt` 和 `requirements/{app_name}.txt`) 安裝到其隔離環境中。
4.  **針對性測試**: 在隔離環境中，只執行該 App 自身的 `pytest` 測試。
5.  **徹底清理**: 測試結束後（無論成功或失敗），自動刪除該 App 的測試虛擬環境。
6.  **統一報告**: 收集所有 App 的測試結果，並在最後提供一個總結報告。

此腳本旨在取代舊的 `run_e2e_tests.sh`，提供一個無副作用、可重複、且易於除錯的測試執行流程。
"""
import os
import subprocess
import sys
from pathlib import Path
import shutil
import time

# --- 常數定義 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
REQUIREMENTS_DIR = PROJECT_ROOT / "requirements"

# --- 輔助函式 ---

def print_header(title: str, char="=", length=80):
    """印出帶有風格的標題"""
    print("\n" + char * length)
    print(f"{title.center(length)}")
    print(char * length)

def run_command(command: list[str], cwd: Path, venv_python: Path = None, env: dict = None) -> tuple[int, str]:
    """
    執行一個 shell 命令並返回其返回碼和合併的輸出。

    Args:
        command: 命令及其參數的列表。
        cwd: 執行的工作目錄。
        venv_python: (可選) 如果提供，則使用此 Python 解譯器。
        env: (可選) 要使用的環境變數。

    Returns:
        一個包含 (返回碼, 合併的 stdout/stderr) 的元組。
    """
    full_command = command
    if venv_python:
        # 將命令中的 'python' 或 'pytest' 替換為虛擬環境中的可執行檔路徑
        # 這比修改 PATH 更明確和穩健
        executable = shutil.which(command[0], path=str(venv_python.parent))
        if not executable:
             raise FileNotFoundError(f"在虛擬環境中找不到可執行檔: {command[0]}")
        full_command = [executable] + command[1:]

    print(f"  > Executing: {' '.join(full_command)}", flush=True)

    start_time = time.time()
    try:
        process_env = os.environ.copy()
        if env:
            process_env.update(env)

        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=cwd,
            env=process_env,
        )

        output_lines = []
        for line in process.stdout:
            print(f"    {line.strip()}", flush=True)
            output_lines.append(line)

        rc = process.wait()
        duration = time.time() - start_time

        if rc != 0:
            print(f"  ❌ FAILED (retcode={rc}, duration={duration:.2f}s)", flush=True)
        else:
            print(f"  ✅ SUCCESS (duration={duration:.2f}s)", flush=True)

        return rc, "".join(output_lines)

    except Exception as e:
        duration = time.time() - start_time
        print(f"  💥 CRITICAL ERROR (duration={duration:.2f}s): {e}", flush=True)
        return 1, str(e)


def test_app(app_path: Path) -> bool:
    """對單一應用程式執行完整的隔離測試流程"""
    app_name = app_path.name
    print_header(f"Testing Application: {app_name}")

    venv_path = app_path / ".venv_test"

    # --- 自動清理機制 ---
    if venv_path.exists():
        print(f"發現舊的測試環境，正在清理: {venv_path}")
        shutil.rmtree(venv_path)

    try:
        # 1. 建立虛擬環境
        print_header("Step 1: Creating isolated virtual environment", char="-")
        ret, _ = run_command(["python", "-m", "venv", str(venv_path)], cwd=PROJECT_ROOT)
        if ret != 0: return False

        python_executable = venv_path / "bin" / "python"

        # 2. 安裝依賴
        print_header("Step 2: Installing dependencies", char="-")
        base_reqs = REQUIREMENTS_DIR / "base.txt"
        app_reqs = REQUIREMENTS_DIR / f"{app_name}.txt"

        # 升級 pip
        ret, _ = run_command(["python", "-m", "pip", "install", "--upgrade", "pip"], cwd=PROJECT_ROOT, venv_python=python_executable)
        if ret != 0: return False

        # 安裝基礎依賴
        ret, _ = run_command(["python", "-m", "pip", "install", "-r", str(base_reqs)], cwd=PROJECT_ROOT, venv_python=python_executable)
        if ret != 0: return False

        # 安裝 App 特定依賴
        if app_reqs.exists():
            ret, _ = run_command(["python", "-m", "pip", "install", "-r", str(app_reqs)], cwd=PROJECT_ROOT, venv_python=python_executable)
            if ret != 0: return False

        # 3. 執行 Pytest
        print_header(f"Step 3: Running pytest for '{app_name}'", char="-")
        # 設定 PYTHONPATH，讓測試可以找到 'src' 模組
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)

        # Pytest 命令現在直接指向 App 的 tests 目錄
        test_dir = app_path / "tests"
        if not test_dir.exists():
            print(f"⚠️  No 'tests' directory found for {app_name}. Skipping.")
            return True # 沒有測試也算成功

        ret, _ = run_command(["pytest", str(test_dir)], cwd=PROJECT_ROOT, venv_python=python_executable)
        if ret != 0:
            return False

        return True

    finally:
        # 4. 清理環境
        print_header("Step 4: Cleaning up environment", char="-")
        if venv_path.exists():
            shutil.rmtree(venv_path)
            print(f"  ✅ Removed virtual environment: {venv_path}")


def main():
    """主函式：發現所有 App 並依次進行測試"""
    print_header("Phoenix Heart - Isolated Test Runner")

    apps_to_test = [p for p in SRC_DIR.iterdir() if p.is_dir() and (p / "main.py").exists()]

    if not apps_to_test:
        print("No runnable apps found in 'src' directory.")
        sys.exit(0)

    results = {}
    all_passed = True

    for app_path in apps_to_test:
        success = test_app(app_path)
        results[app_path.name] = "PASSED" if success else "FAILED"
        if not success:
            all_passed = False

    # --- 總結報告 ---
    print_header("Final Test Report")
    for app_name, status in results.items():
        status_icon = "✅" if status == "PASSED" else "❌"
        print(f"  {status_icon} {app_name:<20} {status}")
    print_header("", char="=")

    if all_passed:
        print("🎉 All applications passed the isolated tests! 🎉")
        sys.exit(0)
    else:
        print("🔥 Some applications failed the isolated tests. Please review logs. 🔥")
        sys.exit(1)

if __name__ == "__main__":
    main()
