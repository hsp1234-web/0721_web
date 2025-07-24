# -*- coding: utf-8 -*-
# 整合型應用平台 Colab 啟動器
# 版本: 3.0.0
# 此腳本的唯一目的是在 Colab 環境中準備並啟動主應用程式 `run.py`。

import sys
from pathlib import Path

def display_source_code(*files: str):
    """
    在 Colab 輸出中顯示指定檔案的原始碼。
    """
    print("=" * 80)
    print("📄 核心腳本原始碼預覽")
    print("=" * 80)
    for file_name in files:
        try:
            content = Path(file_name).read_text(encoding='utf-8')
            print(f"\n--- 檔案: {file_name} ---\n")
            print(content)
            print(f"\n--- 結束: {file_name} ---")
        except FileNotFoundError:
            print(f"\n--- 警告: 找不到檔案 {file_name}，無法顯示。 ---\n")
        except Exception as e:
            print(f"\n--- 錯誤: 讀取檔案 {file_name} 時發生錯誤: {e} ---\n")
    print("=" * 80)
    print("✅ 原始碼預覽結束")
    print("=" * 80, "\n")


def main():
    """
    Colab 環境的主執行流程。
    1. 顯示核心腳本的源碼。
    2. 導入並執行 `run.py` 的主函式。
    """
    # 顯示核心管理和執行腳本的內容
    display_source_code("uv_manager.py", "run.py")

    try:
        # 導入主執行腳本。
        # 假設 run.py 已經處理了所有路徑問題。
        import run

        # 執行主程式，run.py 將處理安裝和啟動的所有邏輯。
        # 我們不傳遞任何參數，讓 run.py 使用其預設行為 (安裝並運行)。
        run.main()

    except ImportError as e:
        print(f"❌ [致命錯誤] 無法導入 'run.py'。請確保該檔案存在於專案根目錄。", file=sys.stderr)
        print(f"詳細錯誤: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ [致命錯誤] 執行 'run.py' 時發生未預期的嚴重錯誤。", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)

# 當此腳本被 Colab `import` 後，直接呼叫 main() 函式。
if __name__ == "__main__":
    main()
else:
    # 為了確保在 Colab 中 "import colab_run" 就能執行
    main()
