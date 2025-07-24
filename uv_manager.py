# -*- coding: utf-8 -*-
import os
import subprocess  # nosec B404
import sys
from typing import List


def install_dependencies() -> bool:
    """使用 uv 快速安裝 requirements.txt 中的所有依賴。"""
    # 確保 uv 已安裝
    try:
        subprocess.run(  # nosec B603
            [sys.executable, "-m", "uv", "--version"], check=True, capture_output=True
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("INFO: 'uv' 未找到，正在安裝...")
        try:
            subprocess.run(  # nosec B603
                [sys.executable, "-m", "pip", "install", "uv"],
                check=True,
                capture_output=True,
            )
            print("SUCCESS: 'uv' 安裝成功。")
        except Exception as e:
            print(f"FATAL: 'uv' 安裝失敗: {e}", file=sys.stderr)
            return False

    # 執行安裝
    requirements_path = "requirements.txt"
    if not os.path.exists(requirements_path):
        print(
            f"ERROR: '{requirements_path}' not found.",
            file=sys.stderr,
        )
        return False

    command: List[str] = [
        sys.executable,
        "-m",
        "uv",
        "pip",
        "sync",
        requirements_path,
    ]
    print(f"INFO: 執行指令: {' '.join(command)}")
    # 使用 Popen 來即時串流輸出，讓使用者能看到安裝過程
    process = subprocess.Popen(  # nosec B603
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
    )

    if process.stdout:
        for line in iter(process.stdout.readline, ""):
            print(line, end="")

    process.wait()

    if process.returncode == 0:
        print("\n--- [uv_manager] 依賴安裝成功 ---")
        return True

    print(
        f"\n--- [uv_manager] 依賴安裝失敗，返回碼: {process.returncode} ---",
        file=sys.stderr,
    )
    return False
