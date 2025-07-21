# colab_launch.py (生產級版本 v2.0)

import os
import sys
import subprocess
import time
from pathlib import Path

# --- 預處理：處理 Colab 環境的特殊性 ---
try:
    from google.colab import output
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
    # 如果不在 Colab 環境，定義一個假的 output 物件以避免腳本錯誤
    class MockOutput:
        def serve_kernel_port_as_window(self, port, anchor_text):
            print("--- 非 Colab 環境 ---")
            print(f"伺服器應在 http://127.0.0.1:{port} 啟動")
            print(f"錨點文字: {anchor_text}")
    output = MockOutput()


# --- 工具箱：經過加固的指令執行器 ---

def run_command(command: list, description: str, working_dir: Path):
    """
    一個通用的指令執行器，強制在指定目錄下工作。

    Args:
        command (list): 要執行的指令列表 (例如: ["poetry", "install"])。
        description (str): 顯示給使用者的進度描述。
        working_dir (Path): 指令執行的工作目錄。
    """
    print(f"🚀 正在執行: {description}...")
    try:
        # 【核心升級】使用 cwd 參數，確保指令在正確的專案根目錄下執行。
        # 這將徹底解決 "pyproject.toml not found" 的問題。
        result = subprocess.run(
            command,
            check=True,          # 如果指令返回非零碼，則會引發錯誤
            capture_output=True, # 捕獲標準輸出與標準錯誤
            text=True,           # 將輸出解碼為文字
            encoding='utf-8',
            cwd=working_dir      # <--- 關鍵的戰術升級：指定工作地圖
        )
        # 為了簡潔，預設不印出成功時的輸出，但保留此處方便除錯
        # print(result.stdout)
        print(f"✅ {description}... 完成。")
    except subprocess.CalledProcessError as e:
        # 當指令執行失敗時，印出詳細的錯誤日誌，然後中止整個流程
        print(f"💥 在執行 '{description}' 時發生致命錯誤:")
        print(f"   - 指令: {' '.join(e.args)}")
        print(f"   - 返回碼: {e.returncode}")
        print(f"   - 標準輸出:\n{e.stdout.strip()}")
        print(f"   - 標準錯誤:\n{e.stderr.strip()}")
        raise  # 重新拋出異常，中止 main 函式


# --- 指揮中心：主部署函式 ---

def main():
    """
    協調整個部署流程。
    """
    project_root = None # 先初始化
    try:
        # 1. 自我定位：找到專案根目錄
        project_root = Path(__file__).parent.resolve()
        print(f"ℹ️ 自動偵測到專案根目錄: {project_root}")

        # 2. 安裝 Poetry (此步驟不需要在專案目錄執行)
        # 為了避免重複安裝，可以做個簡單檢查
        if IN_COLAB:
            os.environ['PATH'] = f"/root/.local/bin:{os.environ['PATH']}"
            run_command(
                ["pip", "install", "poetry"],
                description="安裝 Poetry",
                working_dir=project_root # 在此處 cwd 只是為了統一，非必須
            )

        # 3. 安裝專案依賴 (必須在專案目錄執行)
        run_command(
            ["poetry", "install", "--no-root"],
            description="安裝專案依賴",
            working_dir=project_root # <--- 傳遞工作地圖
        )

        # 4. 在背景啟動伺服器
        print("🚀 正在背景啟動 FastAPI 伺服器...")
        # 使用 Popen 可以在背景執行，並將日誌導向檔案
        log_file = open("server.log", "w")
        subprocess.Popen(
            ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=project_root, # <--- 同樣指定工作地圖
            stdout=log_file,
            stderr=log_file
        )
        time.sleep(5) # 等待伺服器啟動
        print("✅ 伺服器啟動指令已發送，日誌將寫入 server.log。")

        # 5. 產生公開網址
        print("🚀 正在產生公開存取網址...")
        output.serve_kernel_port_as_window(8000, anchor_text="點擊這裡，在新分頁中開啟您的應用程式")
        print("\n👍 部署完成！")

    except Exception as e:
        print(f"\n💥 部署過程中發生未預期的錯誤: {e}")
        if project_root:
            print(f"   - 請檢查位於 '{project_root}' 的 pyproject.toml 設定。")
        sys.exit(1)


# --- 程式進入點 ---
if __name__ == "__main__":
    main()
