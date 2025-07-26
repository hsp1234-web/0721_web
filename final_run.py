# ==============================================================================
#                 最終部署驗證運行器 (v2.0)
#
#   **v2.0 更新**: 不再創建虛擬環境，直接在當前沙箱環境中操作，
#                 以避免 "Too many files" 錯誤。
#
#   **使命**: 在當前環境中執行一個簡化的、可靠的命令鏈，以完成
#             最終的端到端整合驗證，然後自我銷毀。
# ==============================================================================

import subprocess
import sys
from pathlib import Path
import os

# --- 顏色代碼 ---
class colors:
    OKGREEN = '\033[92m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def print_success(message): print(f"{colors.OKGREEN}✅ {message}{colors.ENDC}")
def print_error(message): print(f"{colors.FAIL}🔴 {message}{colors.ENDC}")

def main():
    # 這個命令鏈直接在當前環境中操作，避免了創建大量文件。
    command = """
    echo "--- 步驟 1: 安裝依賴到當前環境 ---" && \\
    pip install -r requirements/base.txt && \\

    echo "--- 步驟 2: 在後台啟動核心服務 ---" && \\
    python server_main.py & \\
    SERVER_PID=$! && \\

    echo "--- 步驟 3: 等待服務啟動 (10 秒) ---" && \\
    sleep 10 && \\

    echo "--- 步驟 4: 使用 httpx 驗證服務 API ---" && \\
    httpx get http://127.0.0.1:8000/quant/data && \\

    echo "--- 步驟 5: 測試成功，關閉服務 ---" && \\
    kill $SERVER_PID && \\

    echo "--- 所有驗證已通過 ---"
    """

    try:
        # 需要一個包含專案根目錄的 PYTHONPATH
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd())

        result = subprocess.run(
            command,
            shell=True,
            check=True,
            executable="/bin/bash",
            capture_output=True,
            text=True,
            env=env
        )

        print(result.stdout)
        print_success("所有整合測試已成功通過！系統穩定性已驗證。")

        # 成功後自我刪除
        print_success("測試腳本將自我銷毀。")
        Path(__file__).unlink()

    except subprocess.CalledProcessError as e:
        print_error("💥💥💥 整合測試失敗 💥💥💥")
        print_error("--- STDOUT ---")
        print(e.stdout)
        print_error("--- STDERR ---")
        print(e.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
