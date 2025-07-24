# -*- coding: utf-8 -*-
import subprocess
import sys
from pathlib import Path

REQUIREMENTS_FILE = "requirements.txt"

def install_dependencies():
    """
    使用 uv 快速安裝 requirements.txt 中的所有依賴。
    """
    # 確保 uv 已安裝
    try:
        subprocess.run([sys.executable, "-m", "uv", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("INFO: 'uv' 未找到，正在安裝...")
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "uv"], check=True, capture_output=True)
            print("SUCCESS: 'uv' 安裝成功。")
        except Exception as e:
            print(f"ERROR: 安裝 'uv' 失敗: {e}", file=sys.stderr)
            return False

    # 檢查 requirements.txt 是否存在
    requirements_path = Path(__file__).parent / REQUIREMENTS_FILE
    if not requirements_path.exists():
        print(f"ERROR: 找不到 '{REQUIREMENTS_FILE}'。跳過依賴安裝。", file=sys.stderr)
        return False

    # 執行安裝命令
    command = [
        sys.executable, "-m", "uv", "pip", "install",
        "-r", str(requirements_path),
        "--no-cache"
    ]

    print(f"INFO: 執行指令: {' '.join(command)}")
    # 使用 Popen 來即時串流輸出，讓使用者能看到安裝過程
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')

    for line in iter(process.stdout.readline, ''):
        print(line, end='')

    process.wait()

    if process.returncode == 0:
        print("\n--- [uv_manager] 所有依賴項均已成功安裝！ ---")
        return True
    else:
        print(f"\n--- [uv_manager] 依賴安裝失敗，返回碼: {process.returncode} ---", file=sys.stderr)
        return False

if __name__ == "__main__":
    if not install_dependencies():
        sys.exit(1)
