import os
import sys
import subprocess
import time
from pathlib import Path

def main():
    """
    v2.0.1 最終實戰演練腳本。
    """
    project_path = Path(__file__).parent.resolve()
    print(f"--- [驗證] 專案路徑: {project_path} ---")

    # 模擬 Colab 儲存格的參數
    params = {
        "--display-lines": "50",
        "--refresh-interval": "1.0",
        "--fastapi-port": "8787",
    }

    # 組合命令
    cmd = [
        sys.executable,
        "-m", "integrated_platform.start_platform",
    ]
    for key, value in params.items():
        cmd.extend([key, value])

    print(f"--- [驗證] 準備執行總指揮: {' '.join(cmd)} ---")

    # 使用 Popen 在背景執行總指揮，並明確傳遞環境變數
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_path) + os.pathsep + env.get("PYTHONPATH", "")
    process = subprocess.Popen(cmd, stdout=sys.stdout, stderr=sys.stderr, env=env)

    print("--- [驗證] 總指揮已啟動，開始監控 60 秒... ---")
    print("--- [驗證] 請觀察下方的日誌輸出是否持續、穩定且無中斷。 ---")

    time.sleep(60)

    print("\n--- [驗證] 監控結束，正在終止所有進程... ---")

    # 終止總指揮進程，它內部的 finally 會負責清理子進程
    process.terminate()
    try:
        process.wait(timeout=10)
        print("--- [驗證] 總指揮進程已成功終止。 ---")
    except subprocess.TimeoutExpired:
        print("--- [驗證警告] 總指揮進程未能及時響應終止信號，將強制終止。 ---")
        process.kill()

    print("--- [驗證] 腳本執行完畢 ---")

if __name__ == "__main__":
    main()
