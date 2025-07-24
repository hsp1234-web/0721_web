# -*- coding: utf-8 -*-
# 整合型應用平台 Colab 啟動器
# 版本: 5.0.0
# 此腳本使用 Google Colab 的內建代理功能，提供一個安全、私有的方式來存取應用程式。

import sys
import threading
import time
from pathlib import Path

# --- 配置 ---
PORT = 8000
HOST = "127.0.0.1"

def _print_header(title: str):
    """印出帶有風格的標頭。"""
    print("\n" + "="*80)
    print(f"🚀 {title}")
    print("="*80)

def main():
    """
    Colab 環境的主執行流程。
    1. 安裝依賴。
    2. 在背景啟動主應用程式。
    3. 使用 google.colab.output 產生內部代理連結。
    """
    # 階段一: 安裝依賴
    _print_header("階段一：安裝依賴")
    try:
        import uv_manager
        if not uv_manager.install_dependencies():
            print("❌ 依賴安裝失敗，終止執行。", file=sys.stderr)
            sys.exit(1)
    except ImportError:
        print("❌ 致命錯誤: 'uv_manager.py' 不存在。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"❌ 在依賴安裝階段發生未預期錯誤: {e}", file=sys.stderr)
        sys.exit(1)

    # 階段二: 啟動主應用程式
    _print_header(f"階段二：啟動主應用程式於 http://{HOST}:{PORT}")

    # 我們需要在一個背景執行緒中啟動 uvicorn，
    # 這樣主執行緒才能繼續執行並呼叫 Colab 的輸出功能。
    try:
        import run
        app_thread = threading.Thread(target=run.main, daemon=True)
        app_thread.start()
        print(f"✅ 主應用程式已在背景執行緒中啟動。")
        time.sleep(5) # 給予伺服器一些啟動時間
    except Exception as e:
        print(f"❌ [致命錯誤] 啟動 'run.py' 時發生嚴重錯誤。", file=sys.stderr)
        import traceback
        print(traceback.format_exc(), file=sys.stderr)
        sys.exit(1)

    # 階段三: 產生 Colab 代理連結
    _print_header("階段三：產生 Colab 內部存取連結")
    try:
        from google.colab import output
        # 這個函式會在 Colab 輸出一個可點擊的連結
        output.serve_kernel_port_as_window(PORT, anchor_text="點此開啟您的應用程式")
        print("✅ 已成功產生應用程式連結。請點擊上方連結開啟。")
    except ImportError:
        print("\n" + "-"*80, file=sys.stderr)
        print("⚠️ 警告：無法導入 'google.colab' 模組。", file=sys.stderr)
        print("這通常意味著您不是在 Google Colab 環境中執行此腳本。", file=sys.stderr)
        print(f"如果這是在本地環境，請手動打開瀏覽器並訪問 http://{HOST}:{PORT}", file=sys.stderr)
        print("-" * 80, file=sys.stderr)
    except Exception as e:
        print(f"❌ 產生 Colab 連結時發生錯誤: {e}", file=sys.stderr)

    # 保持主執行緒活躍
    print("\nℹ️ 服務正在運行中。若要停止，請在 Colab 中斷執行階段。")
    try:
        while True:
            time.sleep(3600)
    except KeyboardInterrupt:
        print("\n🛑 偵測到手動中斷，正在關閉服務...")
        sys.exit(0)

if __name__ == "__main__":
    main()
else:
    # 允許 'import colab_run' 直接執行
    main()
