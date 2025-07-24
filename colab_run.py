# -*- coding: utf-8 -*-
# 整合型應用平台 Colab 啟動器
# 版本: 3.1.0
# 此腳本在 Colab 環境中準備並啟動主應用程式 `run.py`，並自動建立一個公開的 Cloudflare Tunnel 連結。

import sys
import time
import re
import os
import platform
import subprocess
import threading
from pathlib import Path
import urllib.request

# --- 配置 ---
CLOUDFLARED_URL_AMD64 = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64"
CLOUDFLARED_URL_ARM64 = "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-arm64"
CLOUDFLARED_PATH = Path("./cloudflared")
PORT = 8000  # 應與 run.py 中的埠號一致

def _install_cloudflared():
    """
    下載並設定 cloudflared。
    """
    if CLOUDFLARED_PATH.exists():
        print("✅ cloudflared 已存在，跳過下載。")
        return

    print("☁️ 正在下載 Cloudflare Tunnel (cloudflared)...")

    # 根據架構選擇正確的 URL
    arch = platform.machine()
    if "aarch64" in arch or "arm64" in arch:
        url = CLOUDFLARED_URL_ARM64
        print("检测到 ARM64 架構。")
    else:
        url = CLOUDFLARED_URL_AMD64
        print("检测到 AMD64 架構。")

    try:
        urllib.request.urlretrieve(url, CLOUDFLARED_PATH)
        CLOUDFLARED_PATH.chmod(0o755)
        print("✅ cloudflared 下載並設定完成。")
    except Exception as e:
        print(f"❌ 下載 cloudflared 失敗: {e}", file=sys.stderr)
        sys.exit(1)

def _run_cloudflared():
    """
    在背景啟動 cloudflared 並解析輸出以取得公開網址。
    """
    print(f"🚇 正在啟動 Cloudflare Tunnel，將本地埠 {PORT} 公開...")

    # 使用 Popen 在背景執行 cloudflared
    process = subprocess.Popen(
        [str(CLOUDFLARED_PATH), "tunnel", "--url", f"http://127.0.0.1:{PORT}", "--no-autoupdate"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )

    # 等待幾秒鐘讓 cloudflared 初始化並輸出 URL
    time.sleep(3)

    # 從 stderr 讀取輸出以尋找 URL
    # cloudflared 通常會將日誌資訊輸出到 stderr
    for line in iter(process.stderr.readline, ''):
        print(f"   [Cloudflared Log] {line.strip()}") # 顯示日誌方便偵錯
        # 使用正規表示式尋找 https://*.trycloudflare.com
        match = re.search(r"(https?://[a-zA-Z0-9-]+\.trycloudflare\.com)", line)
        if match:
            public_url = match.group(0)
            print("\n" + "="*80)
            print(f"✅ 您的應用程式已上線！")
            print(f"🔗 公開網址: {public_url}")
            print("="*80 + "\n")
            # 找到網址後，我們可以讓這個執行緒繼續執行以保持通道開啟，
            # 但不再需要處理輸出。
            break

    # 讓 cloudflared 程序繼續在背景運行
    # 如果需要，可以添加 process.wait() 來等待它結束

def display_source_code(*files: str):
    """
    在 Colab 輸出中顯示指定檔案的原始碼。
    """
    # 此功能保持不變
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
    2. 安裝 cloudflared。
    3. 在背景執行緒中啟動主應用程式。
    4. 啟動 cloudflared 並顯示公開網址。
    """
    # 顯示核心管理和執行腳本的內容
    display_source_code("uv_manager.py", "run.py")

    # 步驟 1: 安裝 cloudflared
    _install_cloudflared()

    # 步驟 2: 在背景執行緒中啟動主應用程式
    print("🚀 正在背景啟動主應用程式...")
    try:
        import run
        # 我們傳遞 --port 參數以確保與 cloudflared 的配置一致
        app_thread = threading.Thread(target=run.main, daemon=True)
        app_thread.start()
        print("✅ 主應用程式正在背景運行。")
    except ImportError as e:
        print(f"❌ [致命錯誤] 無法導入 'run.py'。請確保該檔案存在於專案根目錄。", file=sys.stderr)
        print(f"詳細錯誤: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ [致命錯誤] 啟動 'run.py' 時發生未預期的嚴重錯誤。", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)

    # 步驟 3: 啟動 cloudflared 並顯示公開網址
    # 這會在主執行緒中運行，以保持 Colab Session 活躍
    _run_cloudflared()

    # 讓主執行緒保持活躍，以維持背景服務
    print("\n⏳ 服務正在運行中。若要停止，請中斷 Colab 執行階段。")
    try:
        while True:
            time.sleep(3600) # 每小時喚醒一次，或直到被中斷
    except KeyboardInterrupt:
        print("\n🛑 偵測到手動中斷，正在關閉服務...")
        sys.exit(0)


# 當此腳本被 Colab `import` 後，直接呼叫 main() 函式。
if __name__ == "__main__":
    main()
else:
    # 為了確保在 Colab 中 "import colab_run" 就能執行
    main()
