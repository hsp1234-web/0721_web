# -*- coding: utf-8 -*-
import argparse
import sys

import uv_manager

def main():
    """
    主執行函數，協調安裝和伺服器啟動。
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
        default=8000,
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
        print("--- [run.py] 階段一：依賴安裝 ---")
        if not uv_manager.install_dependencies():
            sys.exit(1)

    if args.install_only:
        print("--- [run.py] 僅安裝模式，任務完成。 ---")
        sys.exit(0)

    print(f"\n--- [run.py] 階段二：在 {args.host}:{args.port} 啟動應用伺服器 ---")
    import uvicorn
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
