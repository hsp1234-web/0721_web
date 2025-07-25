# ==============================================================================
#                      核心服務啟動器 (Core Service Launcher)
#
#   此腳本是專為生產環境和 Colab 環境設計的、極簡的服務啟動器。
#
#   其唯一職責是：
#   - 解析命令列傳入的 --host 和 --port 參數。
#   - 使用 uvicorn 以阻塞模式，長期運行主 FastAPI 應用 (`main:app`)。
#
#   這確保了它作為一個子進程時，能夠保持存活，從而讓父進程
#   (如 colab_run.py) 的監控迴圈可以持續運作。
#
# ==============================================================================

import argparse
import uvicorn

def main():
    """
    解析命令列參數並啟動 Uvicorn 伺服器。
    """
    parser = argparse.ArgumentParser(description="鳳凰之心核心服務啟動器")
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="伺服器監聽的主機位址"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="伺服器監聽的埠號"
    )
    args = parser.parse_args()

    print(f"🚀 [server_main] 準備在 {args.host}:{args.port} 上啟動 FastAPI 應用...")

    # 這是一個阻塞式呼叫，會一直運行直到進程被終止
    uvicorn.run(
        "main:app",
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
