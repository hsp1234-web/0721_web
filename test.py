#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
test.py - 完整測試與品質預檢啟動器

此腳本執行一個完整的測試與檢查流程，包括：
1.  程式碼品質與靜態分析 (透過 pre-commit)。
2.  核心功能測試 (透過 pytest)。
3.  測試覆蓋率報告 (透過 coverage.py)。

這是用於 CI/CD 或提交前最終把關的腳本。
"""

import subprocess
import sys


def run_command(command: list[str], title: str) -> bool:
    """運行一個命令並打印標題和結果。"""
    print("\n" + "=" * 60)
    print(f"🧪 正在執行: {title}")
    print("=" * 60)
    print(f"▶️  {' '.join(command)}")

    result = subprocess.run(command, check=False)

    if result.returncode == 0:
        print(f"✅ 成功: {title} 通過。")
        return True

    print(f"❌ 失敗: {title} 未通過 (返回碼: {result.returncode})。", file=sys.stderr)
    return False


def main() -> None:
    """主執行函數。"""
    all_passed = True

    # --- 步驟 1: 執行 Pre-commit 靜態分析 ---
    pre_commit_passed = run_command(
        ["pre-commit", "run", "--all-files"], "程式碼品質與靜態分析 (pre-commit)"
    )
    if not pre_commit_passed:
        all_passed = False
        print("\nINFO: 由於靜態分析失敗，建議先修復上述問題。")
        # 在 CI 環境中，這裡可以直接退出：
        # sys.exit(1)

    # --- 步驟 2: 執行 Pytest 功能測試與覆蓋率 ---
    # 即使靜態分析失敗，我們仍然可以運行測試，以獲得更多資訊。
    pytest_command = [
        "pytest",
        "--cov",  # 啟用覆蓋率
        "--cov-report=term-missing",  # 在終端顯示報告和缺失的行
        # 注意: fail_under 在 pyproject.toml 中配置
    ]
    pytest_passed = run_command(
        pytest_command, "功能測試與覆蓋率檢查 (pytest & coverage)"
    )
    if not pytest_passed:
        all_passed = False

    # --- 總結 ---
    print("\n" + "=" * 60)
    print("📋 完整測試流程總結")
    print("=" * 60)

    if all_passed:
        print("🎉🎉🎉 恭喜！所有檢查和測試均已通過！🎉🎉🎉")
        sys.exit(0)
    else:
        print("🔥 部分檢查或測試失敗，請檢查上面的日誌輸出。")
        sys.exit(1)


if __name__ == "__main__":
    main()
