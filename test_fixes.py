import sys
import subprocess
import json
from pathlib import Path
import os
import shutil

# --- Constants ---
PROJECT_ROOT = Path(__file__).parent.resolve()
APPS_DIR = PROJECT_ROOT / "apps"
CONFIG_FILE = PROJECT_ROOT / "config.json"
DB_FILE = PROJECT_ROOT / "test_gunicorn.db"

# --- Color Codes ---
class C:
    GREEN = "\033[92m"
    FAIL = "\033[91m"
    END = "\033[0m"
    BOLD = "\033[1m"

def print_success(msg):
    print(f"{C.GREEN}{C.BOLD}✅ {msg}{C.END}")

def print_fail(msg):
    print(f"{C.FAIL}{C.BOLD}❌ {msg}{C.END}")

def print_info(msg):
    print(f"\033[96mℹ️ {msg}{C.END}")

def cleanup():
    """Clean up generated files and directories."""
    print_info("\n--- 執行清理 ---")
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
    if DB_FILE.exists():
        DB_FILE.unlink()
    # Remove any temp reqs file
    temp_reqs = PROJECT_ROOT / "temp_reqs.txt"
    if temp_reqs.exists():
        temp_reqs.unlink()


def test_gunicorn_fix():
    """
    測試案例 1：驗證 launch.py 中的 Gunicorn 啟動問題是否已修復。
    """
    print("\n--- 測試案例 1: 驗證 Gunicorn 啟動修復 ---")

    # 1. 建立一個假的 config.json 來觸發完整模式
    config = {"FAST_TEST_MODE": False, "TIMEZONE": "Asia/Taipei"}
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f)

    # 2. 執行 launch.py。我們只關心 main_dashboard 的啟動
    # 我們可以透過非同步方式只執行第一個 app 的生命週期，但為了簡單起見，
    # 我們完整執行 launch.py，並設定一個短的逾時。
    command = [
        sys.executable,
        str(PROJECT_ROOT / "scripts" / "launch.py"),
        "--db-file", str(DB_FILE)
    ]

    print_info(f"執行命令: {' '.join(command)}")
    try:
        # 我們預期這個腳本會長時間運行，所以我們用 Popen 並在短時間後終止它。
        # 我們主要檢查啟動過程中是否出現 Gunicorn 'No such file' 的錯誤。
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')

        output = ""
        try:
            # 等待 30 秒，讓它有足夠時間安裝和啟動
            output = process.communicate(timeout=30)[0]
        except subprocess.TimeoutExpired:
            process.terminate()
            output = process.communicate()[0]
            print_info("程序逾時並被終止（這是預期行為）")

        if "No such file or directory" in output and "gunicorn" in output:
            print_fail("測試失敗！輸出中仍然包含 Gunicorn 找不到的錯誤。")
            print(output)
            return False

        if "管理應用 'main_dashboard' 時發生嚴重錯誤" in output:
            print_fail("測試失敗！管理 main_dashboard 時發生嚴重錯誤。")
            print(output)
            return False

        print_success("測試通過！在啟動過程中未檢測到 Gunicorn 找不到檔案的錯誤。")
        return True

    except Exception as e:
        print_fail(f"執行 launch.py 時發生未預期的例外狀況: {e}")
        return False

def test_unified_installer():
    """
    測試案例 2：驗證 smart_e2e_test.py 的統一依賴安裝邏輯。
    """
    print("\n--- 測試案例 2: 驗證統一依賴安裝邏輯 ---")

    # 我們需要從 smart_e2e_test.py 導入函式
    # 為了避免複雜的 sys.path 操作，我們直接執行它的一部分邏輯
    try:
        from scripts.smart_e2e_test import discover_apps, install_all_app_dependencies, run_command

        apps = discover_apps()
        # 我們在 mock 模式下執行，以避免安裝大型依賴
        result = install_all_app_dependencies(apps, "mock")

        if result:
            print_success("測試通過！統一依賴安裝程序成功執行並返回 True。")
            # 可以額外檢查某個套件是否真的被安裝
            try:
                subprocess.check_output([sys.executable, "-m", "pip", "show", "fastapi"])
                print_success("驗證成功：fastapi 套件已安裝。")
                return True
            except subprocess.CalledProcessError:
                print_fail("驗證失敗：fastapi 套件未安裝。")
                return False
        else:
            print_fail("測試失敗！統一依賴安裝程序返回 False。")
            return False

    except Exception as e:
        print_fail(f"執行統一安裝邏輯時發生未預期的例外狀況: {e}")
        return False

def main():
    """主執行函數"""
    # 為了讓 import 成功，需要將專案根目錄加入 path
    sys.path.insert(0, str(PROJECT_ROOT))

    all_passed = True
    try:
        if not test_unified_installer():
            all_passed = False
        cleanup()
        if not test_gunicorn_fix():
            all_passed = False
    finally:
        cleanup()

    if all_passed:
        print_success("\n🎉 所有修復驗證測試均已通過！")
        sys.exit(0)
    else:
        print_fail("\n💀 部分修復驗證測試失敗。")
        sys.exit(1)

if __name__ == "__main__":
    main()
