# -*- coding: utf-8 -*-
# 最終作戰計畫 P8：鳳凰之心
# 本地端驗證腳本 (colab_test.py)

import sys
import os

def main():
    """
    此腳本的唯一職責是：在一個標準的、非 Colab 的環境中，
    直接導入並執行核心引擎 `core_run.main()`。

    它的目的是證明 `core_run.py` 可以在任何具備 Poetry 環境的
    標準 Linux 系統下，獨立、穩定地啟動並運行，無需任何
    Colab 的 API 或前端模擬。
    """
    print("="*80)
    print("🚀 執行本地端核心引擎驗證 (colab_test.py)")
    print("="*80)
    print("🔵 [資訊] 此腳本將直接啟動核心引擎 `core_run.py`。")
    print("🔵 [資訊] 目標：驗證核心引擎在非 Colab 環境下的獨立運行能力。")
    print("🔵 [資訊] 按下 Ctrl+C 來手動停止伺服器。")
    print("-"*80)

    try:
        # 核心：導入並執行核心引擎的主函式
        import core_run
        core_run.main()

    except ImportError as e:
        print(f"🔴 [錯誤] 導入 `core_run` 失敗: {e}")
        print("🔴 [錯誤] 請確認您是否在 Poetry 環境中執行此腳本。")
        print("🔴 [錯誤] 請先執行 `bash run.sh`，然後執行 `poetry run python colab_test.py`。")
        sys.exit(1)
    except (KeyboardInterrupt, SystemExit):
        print("\n🔵 [資訊] 收到使用者中斷請求，程序正常結束。")
    except Exception as e:
        import traceback
        print(f"🔴 [嚴重錯誤] 執行 `core_run.main()` 時發生未預期的錯誤: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
