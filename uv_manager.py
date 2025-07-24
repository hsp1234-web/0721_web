# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

REQUIREMENTS_FILE = "requirements.txt"

def install_dependencies():
    """
    使用 uv 安裝 requirements.txt 中的所有依賴。
    """
    print("--- [uv_manager] 開始安裝依賴 ---")

    # 確保 uv 已安裝
    try:
        subprocess.run([sys.executable, "-m", "uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("INFO: 未找到 'uv'，正在嘗試安裝...")
        subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True, capture_output=True)
        print("SUCCESS: 'uv' 安裝成功。")

    requirements_path = Path(__file__).parent / REQUIREMENTS_FILE
    if not requirements_path.exists():
        print(f"ERROR: 找不到 '{REQUIREMENTS_FILE}'。跳過安裝。", file=sys.stderr)
        return False

    command = [
        sys.executable, "-m", "uv", "pip", "install",
        "-r", str(requirements_path),
        "--no-cache"
    ]

    print(f"INFO: 執行指令: {' '.join(command)}")
    result = subprocess.run(command)

    if result.returncode == 0:
        print("--- [uv_manager] 所有依賴項均已成功安裝！ ---")
        return True
    else:
        print(f"--- [uv_manager] 依賴安裝失敗，返回碼: {result.returncode} ---", file=sys.stderr)
        return False

if __name__ == "__main__":
    if not install_dependencies():
        sys.exit(1)
