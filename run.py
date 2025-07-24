import argparse

import uvicorn

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Uvicorn 伺服器啟動器")
    parser.add_argument("--host", type=str, default="127.0.0.1", help="綁定的主機地址")
    parser.add_argument("--port", type=int, default=8000, help="監聽的埠號")
    parser.add_argument(
        "--reload", action="store_true", help="啟用熱重載模式 (僅供開發使用)"
    )
    args = parser.parse_args()

    print("[伺服器啟動器] 準備以 Uvicorn 啟動 'main:app'...")
    print(f"[伺服器啟動器] 地址: {args.host}:{args.port}")
    print(f"[伺服器啟動器] 熱重載: {'啟用' if args.reload else '關閉'}")

    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info",
    )
