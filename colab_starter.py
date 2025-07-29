# -*- coding: utf-8 -*-
"""
🚀 鳳凰之心 Colab 啟動器 (Phoenix Heart Colab Starter) v9.2 🚀

此腳本專為 Google Colab 環境設計，作為 `phoenix_starter.py` 的入口點。
它會處理所有 Colab 特有的環境設定，包括：
1.  下載並安裝 `ttyd`，一個能將終端機應用程式投影到網頁的工具。
2.  偵測 Colab 環境，並設定相應的參數。
3.  使用 `ttyd` 來包裹並執行 `phoenix_starter.py`。
4.  將 `ttyd` 產生的網頁介面嵌入到 Colab 的輸出儲存格中，提供無縫的 TUI 體驗。
"""

import os
import sys
import subprocess
import platform
import asyncio
from pathlib import Path
from IPython.display import display, HTML

# --- 常數與設定 ---
PROJECT_ROOT = Path(__file__).parent.resolve()
TTYD_PORT = 7681

def is_running_in_colab():
    """檢查當前是否在 Google Colab 環境中"""
    return "google.colab" in sys.modules

async def download_and_install_ttyd():
    """下載並安裝 ttyd 到 Colab 環境"""
    print("📥 正在下載並設定 ttyd...")
    try:
        # 根據 Colab 的架構 (通常是 x86_64) 下載 ttyd
        url = "https://github.com/tsl0922/ttyd/releases/download/1.7.4/ttyd.x86_64"
        ttyd_path = PROJECT_ROOT / "ttyd"
        subprocess.run(["wget", "-O", str(ttyd_path), url], check=True)
        subprocess.run(["chmod", "+x", str(ttyd_path)], check=True)
        print("✅ ttyd 已成功安裝。")
        return ttyd_path
    except subprocess.CalledProcessError as e:
        print(f"❌ ttyd 下載或設定失敗: {e}")
        return None

async def launch_ttyd_for_phoenix(ttyd_path: Path):
    """使用 ttyd 啟動 phoenix_starter.py"""
    print("🚀 正在透過 ttyd 啟動鳳凰之心指揮中心...")
    command = [
        str(ttyd_path),
        "--port", str(TTYD_PORT),
        "--writable",
        # 將所有客戶端連接到同一個 TUI 實例
        "--one-time",
        "python", str(PROJECT_ROOT / "phoenix_starter.py"),
        "--non-interactive"
    ]

    # 在背景啟動 ttyd 伺服器
    process = await asyncio.create_subprocess_exec(
        *command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )

    # 等待 ttyd 伺服器就緒
    await asyncio.sleep(3) # 給 ttyd 一點啟動時間

    print("✅ ttyd 伺服器已在背景啟動。")
    return process

def display_tui_in_colab():
    """在 Colab 輸出儲存格中嵌入 ttyd 的網頁介面"""
    # 使用 Google Colab 的 output 模組來獲取代理 URL
    from google.colab import output
    proxy_url = output.eval_js(f"google.colab.kernel.proxyPort({TTYD_PORT})")

    # 嵌入 IFrame
    display(HTML(f"""
        <style>
            iframe {{
                width: 100%;
                height: 600px;
                border: 1px solid #ccc;
                border-radius: 5px;
            }}
        </style>
        <iframe src="{proxy_url}"></iframe>
    """))
    print("🎉 鳳凰之心指揮中心已成功嵌入下方！")
    print("您現在可以像在本地終-端機一樣與其互動。")


async def main():
    """Colab 啟動器主函式"""
    if not is_running_in_colab():
        print("此腳本僅設計在 Google Colab 環境中運行。")
        # 如果不在 Colab，直接執行 phoenix_starter.py
        os.execvp("python", ["python", str(PROJECT_ROOT / "phoenix_starter.py")])
        return

    ttyd_path = await download_and_install_ttyd()
    if not ttyd_path:
        return

    ttyd_process = await launch_ttyd_for_phoenix(ttyd_path)
    display_tui_in_colab()

    # 保持腳本運行，直到 ttyd 結束
    await ttyd_process.wait()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 使用者中斷。正在關閉服務...")
    except Exception as e:
        print(f"💥 發生未預期的錯誤: {e}")
