# -*- coding: utf-8 -*-
"""
🚀 鳳凰之心 Colab 啟動器 🚀

此腳本專為在 Google Colab 環境中啟動鳳凰之心專案的儀表板而設計。

它會自動處理以下任務：
1.  **安裝依賴**: 安裝 `uv` 和其他必要的 Python 套件。
2.  **下載 GoTTY**: 從專案的 `tools` 目錄中找到 `gotty`。
3.  **準備環境**: 執行 `scripts/launch.py --prepare-only` 來為所有應用程式建立虛擬環境和安裝依賴。
4.  **啟動儀表板服務**: 在背景啟動 `phoenix_dashboard.py`，並透過 `gotty` 將其轉為 Web 服務。
5.  **代理並嵌入**: 使用 `google.colab.kernel.proxyPort` 產生一個安全的公開網址，並將其嵌入到 IFrame 中，以便在 Colab 儲存格中直接顯示。
"""
import subprocess
import os
import sys
import threading
from pathlib import Path
from IPython.display import display, IFrame
from google.colab import output
from google.colab.kernel import proxyPort

# --- 設定 ---
PROJECT_ROOT = Path("/content/phoenix_heart") # 假設專案被複製到 /content/phoenix_heart
DASHBOARD_PORT = 8080

def run_command(command, cwd=None):
    """執行命令並顯示輸出"""
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        cwd=cwd
    )
    for line in iter(process.stdout.readline, ''):
        print(line.strip())
    process.wait()
    return process.returncode

def main():
    """主執行函數"""
    # 確保我們在正確的目錄
    if not PROJECT_ROOT.exists():
        print(f"❌ 錯誤: 專案目錄 {PROJECT_ROOT} 不存在。")
        print("請先將專案 clone 到 Colab 環境中。")
        # 為了方便，我們在這裡直接 clone
        print("正在自動 clone 專案...")
        run_command(["git", "clone", "https://github.com/your-repo/phoenix-heart.git", str(PROJECT_ROOT)])
        os.chdir(PROJECT_ROOT)

    # 1. 安裝 uv
    print("--- 1. 安裝 uv ---")
    run_command([sys.executable, "-m", "pip", "install", "uv"])

    # 2. 準備所有應用程式的環境
    print("\n--- 2. 準備應用程式環境 ---")
    launch_script = PROJECT_ROOT / "scripts" / "launch.py"
    run_command([sys.executable, str(launch_script), "--prepare-only"])

    # 3. 啟動儀表板
    print(f"\n--- 3. 在背景啟動儀表板 (埠 {DASHBOARD_PORT}) ---")
    dashboard_thread = threading.Thread(
        target=run_command,
        args=([sys.executable, str(launch_script), "--dashboard"],)
    )
    dashboard_thread.daemon = True
    dashboard_thread.start()
    print("儀表板服務已在背景執行緒中啟動。")

    # 4. 顯示 IFrame
    print(f"\n--- 4. 產生並顯示 Colab IFrame ---")
    # 清除之前的輸出並顯示 IFrame
    with output.capture(clear_output=True, wait=True):
        proxy_url = proxyPort(DASHBOARD_PORT, '127.0.0.1')
        print(f"✅ 您的儀表板已就緒！")
        display(IFrame(src=proxy_url, width='100%', height=600))

if __name__ == "__main__":
    main()
