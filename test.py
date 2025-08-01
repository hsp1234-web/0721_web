# -*- coding: utf-8 -*-
"""
鳳凰之心統一測試執行器

此腳本作為專案的單一測試入口點，旨在提供一個簡單、一致的方式來運行所有類型的測試。
它會直接調用主要的端對端(E2E)測試腳本，該腳本負責協調所有子測試。
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """執行主要的 E2E 測試腳本。"""
    project_root = Path(__file__).parent.resolve()
    test_script_path = project_root / "tests" / "test_e2e_main.py"

    if not test_script_path.is_file():
        print(f"❌ 嚴重錯誤：找不到主測試腳本 '{test_script_path}'。")
        sys.exit(1)

    print("="*80)
    print("🚀 鳳凰之心統一測試執行器")
    print(f"▶️  專案根目錄: {project_root}")
    print(f"▶️  執行主測試腳本: {test_script_path}")
    print("="*80)

    # 設定環境變數，以便子腳本能找到模組
    env = os.environ.copy()
    current_pythonpath = env.get("PYTHONPATH", "")
    new_pythonpath = os.pathsep.join([str(project_root), current_pythonpath]) if current_pythonpath else str(project_root)
    env["PYTHONPATH"] = new_pythonpath

    command = [sys.executable, str(test_script_path)]

    try:
        # 不使用 check=True，以便我們可以自己控制退出碼
        result = subprocess.run(command, env=env)

        print("\n" + "="*80)
        if result.returncode == 0:
            print("✅ 主測試腳本執行成功！")
        else:
            print(f"❌ 主測試腳本執行失敗，返回碼: {result.returncode}。")
        print("="*80)

        sys.exit(result.returncode)

    except Exception as e:
        print(f"\n❌ 執行測試時發生未預期的錯誤: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
