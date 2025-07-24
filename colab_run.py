# 檔案: colab_run.py
# 說明: 此腳本為輕量點火器，僅負責傳遞參數並啟動主引擎。

import sys
import subprocess
from pathlib import Path
import traceback

# --- 全域變數 ---
# 說明: 這些變數將由 Colab Notebook 的 @param 表單直接賦值。
#       它們是從駕駛艙到點火器的唯一通訊方式。
LOG_DISPLAY_LINES = 50
STATUS_REFRESH_INTERVAL = 0.2
TARGET_FOLDER_NAME = "WEB"
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔"
FASTAPI_PORT = 8000

def main():
    """
    此主函式負責：
    1. 定位主引擎腳本。
    2. 驗證其存在。
    3. 將全域變數序列化為命令列參數。
    4. 使用參數啟動主引擎。
    """
    try:
        # 1. 定位引擎
        project_path = Path.cwd()
        bootstrap_script = project_path / "colab_bootstrap.py"

        # 2. 前置驗證
        if not bootstrap_script.exists():
            print(f"❌ 致命錯誤：找不到主引擎腳本 'colab_bootstrap.py'。", file=sys.stderr)
            print(f"   請確認該檔案存在於 '{project_path}' 中。", file=sys.stderr)
            sys.exit(1)

        # 3. 構建指令
        command = [
            sys.executable,
            str(bootstrap_script),
            "--log-lines", str(LOG_DISPLAY_LINES),
            "--refresh-interval", str(STATUS_REFRESH_INTERVAL),
            "--target-folder", TARGET_FOLDER_NAME,
            "--archive-folder", ARCHIVE_FOLDER_NAME,
            "--port", str(FASTAPI_PORT),
        ]

        print("🚀 點火器已啟動，正在移交控制權給主引擎...")
        print(f"傳遞參數: {' '.join(command[2:])}")
        print("-" * 50)

        # 5. 點火
        # 使用 Popen 而不是 run，以避免阻塞，並允許主引擎完全接管輸出。
        # 在 Colab 環境中，主腳本的輸出會自然顯示。
        process = subprocess.Popen(command, stdout=sys.stdout, stderr=sys.stderr, text=True, encoding='utf-8')

        # 等待主引擎進程結束。這使得 Colab cell 會保持執行狀態直到引擎關閉或被中斷。
        process.wait()

    except KeyboardInterrupt:
        print("\n🟡 偵測到手動中斷指令。點火器已終止。")
        # 主引擎的 atexit 清理應該會被觸發
    except Exception as e:
        print(f"💥 點火器執行時發生未預期的錯誤: {e}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
