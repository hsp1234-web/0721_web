# -*- coding: utf-8 -*-
import argparse
import uvicorn
import logging
from pathlib import Path

# --- 設定日誌 ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """
    一個極簡的伺服器啟動器。
    它只負責根據傳入的參數啟動 Uvicorn，不處理任何其他邏輯。
    依賴安裝等任務由主引擎 (colab_bootstrap.py) 負責。
    """
    parser = argparse.ArgumentParser(description="核心應用伺服器啟動器。")
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="指定伺服器運行的埠號。"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1", # 改為 127.0.0.1 以符合 Colab 埠號轉發的最佳實踐
        help="指定伺服器監聽的主機地址。"
    )
    parser.add_argument(
        "--app-dir",
        type=str,
        default=".",
        help="指定包含 main:app 的應用程式目錄的相對路徑。"
    )
    args = parser.parse_args()

    # FastAPI 應用的位置，例如 'main:app'
    # 我們假設主應用程式檔案總是命名為 main.py
    app_string = f"{Path(args.app_dir).name}.main:app"

    # 在 Colab 環境下，uvicorn 需要從 /content 目錄下執行
    # 我們的啟動腳本 (colab_bootstrap.py) 已經在專案的根目錄了
    # 所以這裡我們直接使用 uvicorn

    logger.info(f"準備在 {args.host}:{args.port} 上啟動應用...")
    logger.info(f"目標應用: {app_string}")

    # 這裡我們不再需要改變 sys.path，因為主引擎已經處理了
    # 我們假設 colab_bootstrap.py 在啟動此腳本時，工作目錄是正確的

    uvicorn.run(
        "main:app", # 主應用程式始終是根目錄下的 main.py
        host=args.host,
        port=args.port,
        log_level="info"
    )

if __name__ == "__main__":
    main()
