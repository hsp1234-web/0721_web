# -*- coding: utf-8 -*-
import argparse
import sys
import logging

# 嘗試從 colab_run 導入 PORT，如果失敗則使用預設值
try:
    import colab_run
    DEFAULT_PORT = colab_run.PORT
except (ImportError, AttributeError):
    DEFAULT_PORT = 8000

import uv_manager

def main():
    """
    主執行函數，協調安裝和伺服器啟動。
    所有輸出都透過 logging 模組，以便被 colab_run 捕捉。
    """
    parser = argparse.ArgumentParser(description="模組化平台啟動器。")
    parser.add_argument(
        "--install-only",
        action="store_true",
        help="僅執行依賴安裝，然後退出。"
    )
    parser.add_argument(
        "--run-only",
        action="store_true",
        help="僅啟動伺服器，跳過依賴安裝。"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help="指定伺服器運行的埠號。"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="指定伺服器監聽的主機地址。"
    )
    args, unknown = parser.parse_known_args()

    if not args.run_only:
        logging.info("--- [run.py] 階段一：依賴安裝 ---")
        if not uv_manager.install_dependencies():
            logging.error("依賴安裝失敗，終止執行。")
            sys.exit(1)

    if args.install_only:
        logging.info("--- [run.py] 僅安裝模式，任務完成。 ---")
        sys.exit(0)

    logging.info(f"--- [run.py] 階段二：在 {args.host}:{args.port} 啟動應用伺服器 ---")
    try:
        import uvicorn
        # Uvicorn 會自動使用根記錄器的設定
        uvicorn.run(
            "main:app",
            host=args.host,
            port=args.port
        )
    except Exception as e:
        logging.critical(f"Uvicorn 伺服器啟動失敗: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # 為了讓 run.py 也可以獨立執行，我們在這裡也設定一個基本的日誌
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    main()
