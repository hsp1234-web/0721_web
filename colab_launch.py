# colab_launch.py

# --- 階段 1: 導入核心模組 ---
import os
import sys
import subprocess
import time
from pathlib import Path

try:
    from google.colab import output
except ImportError:
    class MockOutput:
        def serve_kernel_port_as_window(self, port, anchor_text):
            print(f"--- 非 Colab 環境 ---")
            print(f"伺服器應在 http://127.0.0.1:{port} 啟動")
            print(f"錨點文字: {anchor_text}")
    output = MockOutput()

# --- 階段 2: 定義輔助函式 (工具箱) ---

def run_command(command: list, description: str):
    """
    職責：一個通用的指令執行器。
    目的：執行 shell 指令，並提供即時的進度回饋與錯誤處理。
    """
    print(f"🚀 正在執行: {description}...")
    try:
        subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(f"💥 在執行 '{description}' 時發生錯誤:")
        print(f"返回碼: {e.returncode}")
        print(f"標準輸出: {e.stdout}")
        print(f"標準錯誤: {e.stderr}")
        sys.exit(1)
    print(f"✅ {description}... 完成。")

# --- 階段 3: 定義主函式 (作戰指揮中心) ---

def main():
    """
    職責： orchestrate the entire deployment process.
    """
    try:
        # 1. 自我定位：找到專案根目錄
        project_root = Path(__file__).parent.resolve()
        print(f"ℹ️ 自動偵測到專案根目錄: {project_root}")

        # 2. 切換工作目錄：確保所有後續指令都在正確的位置執行
        os.chdir(project_root)
        print(f"✅ 已將工作目錄切換至專案根目錄。")

        # 3. 安裝 Poetry
        run_command(
            ["pip", "install", "poetry"],
            description="安裝 Poetry"
        )
        # 將 poetry 加入環境變數
        os.environ['PATH'] = f"/root/.local/bin:{os.environ['PATH']}"

        # 4. 安裝專案依賴
        run_command(
            ["poetry", "install", "--no-root"],
            description="安裝專案依賴"
        )

        # 5. 在背景啟動伺服器
        print("🚀 正在背景啟動 FastAPI 伺服器...")
        with open("server.log", "w") as log_file:
            subprocess.Popen(
                ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
                stdout=log_file,
                stderr=log_file,
            )
        time.sleep(5) # 等待伺服器啟動
        print("✅ 伺服器啟動指令已發送。")

        # 6. 產生公開網址
        print("🚀 正在產生公開存取網址...")
        output.serve_kernel_port_as_window(8000, anchor_text="點擊這裡，在新分頁中開啟您的應用程式")
        print("\n👍 部署完成！")

    except Exception as e:
        # 全域的錯誤捕捉
        print(f"💥 部署過程中發生致命錯誤: {e}")
        sys.exit(1)

# --- 階段 4: 程式進入點 ---
if __name__ == "__main__":
    main()
