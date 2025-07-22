# tests/test_capabilities.py
# -*- coding: utf-8 -*-
"""
功能契約測試
本檔案的唯一職責，就是驗證 README.md 中記錄的每一條指令都能如預期般執行。
"""
import subprocess
from pathlib import Path

# 定義 integrated_platform 的路徑
PROJECT_PATH = Path(__file__).parent.parent / "integrated_platform"

def test_hello_command_capability():
    """
    驗證 `commander_console.py hello` 指令。
    此測試直接對應 README.md 中的「1. 驗證控制台」。
    """
    # 執行 README 中的命令
    result = subprocess.run(
        ["poetry", "run", "python", "src/commander_console.py"],
        cwd=PROJECT_PATH,
        capture_output=True,
        text=True,
        encoding='utf-8',
        check=True
    )

    # 驗證輸出是否符合預期
    expected_output = "你好, 指揮官！控制台已準備就緒。\n"
    assert result.stdout == expected_output, f"預期輸出 '{expected_output}', 但實際得到 '{result.stdout}'"
