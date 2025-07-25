# -*- coding: utf-8 -*-
import os
import subprocess
import sys
from pathlib import Path

# --- 測試設定 ---
TARGET_DIR = "WEB_TEST"
# 使用絕對路徑來避免混淆
target_path = Path.cwd() / TARGET_DIR

# --- 測試主體 ---
def run_test():
    print(f"--- 開始測試：{target_path} ---")

    if not target_path.is_dir():
        print(f"錯誤：測試目錄 '{target_path}' 不存在。", file=sys.stderr)
        return False

    try:
        # 步驟 1: 定義命令的執行目錄
        cwd = str(target_path.resolve())
        print(f"將在以下目錄執行命令: {cwd}")

        # 步驟 2: 安裝依賴
        print("\n--- 正在安裝依賴... ---")
        # 我們需要先安裝 uv
        subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True, capture_output=True)
        install_command = [sys.executable, "-m", "uv", "pip", "sync", "requirements.txt"]
        install_result = subprocess.run(install_command, capture_output=True, text=True, check=True, cwd=cwd)
        print(install_result.stdout)
        print(install_result.stderr)
        print("--- 依賴安裝成功 ---")

        # 步驟 3: 執行應用程式 (驗證導入)
        print("\n--- 正在執行應用程式... ---")
        run_command = [sys.executable, "run.py"]
        run_result = subprocess.run(run_command, capture_output=True, text=True, check=True, cwd=cwd)
        print(run_result.stdout)
        print(run_result.stderr)
        print("--- 應用程式執行成功 ---")

        if "SUCCESS: pydantic_settings 導入成功。" in run_result.stdout:
            print("\n✅✅✅【測試通過】✅✅✅")
            return True
        else:
            print("\n❌❌❌【測試失敗】❌❌❌")
            print("錯誤：未在輸出中找到預期的成功訊息。")
            return False

    except FileNotFoundError as e:
        print(f"錯誤：找不到檔案或目錄 - {e}", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"錯誤：子進程執行失敗，返回碼 {e.returncode}", file=sys.stderr)
        print("--- STDOUT ---", file=sys.stderr)
        print(e.stdout, file=sys.stderr)
        print("--- STDERR ---", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return False
    except Exception as e:
        print(f"發生未預期的錯誤: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if run_test():
        sys.exit(0)
    else:
        sys.exit(1)
