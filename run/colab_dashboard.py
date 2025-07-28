# -*- coding: utf-8 -*-
"""
🚀 鳳凰之心 Colab 儀表板啟動器 🚀

此腳本專為在 Google Colab 環境中啟動鳳凰之心專案的儀表板而設計。
"""
import subprocess
import sys
import threading
from pathlib import Path
from IPython.display import display, IFrame
from google.colab import output
from google.colab.kernel import proxyPort

# --- 設定 ---
PROJECT_ROOT = Path("/content/phoenix_heart")
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
    if not PROJECT_ROOT.exists():
        print("❌ 錯誤: 專案目錄不存在。")
        return

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
    print("\n--- 4. 產生並顯示 Colab IFrame ---")
    with output.capture(clear_output=True, wait=True):
        proxy_url = proxyPort(DASHBOARD_PORT, '127.0.0.1')
        print("✅ 您的儀表板已就緒！")
        display(IFrame(src=proxy_url, width='100%', height=600))

if __name__ == "__main__":
    main()
