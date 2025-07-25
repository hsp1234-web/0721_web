import argparse
import uvicorn
from main import app
from logger.main import setup_logging
from core.config import settings

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="啟動鳳凰之心後端伺服器。")
    parser.add_argument(
        "--log-file",
        type=str,
        default=None,
        help="指定日誌檔案的名稱。"
    )
    args = parser.parse_args()

    # 在啟動 uvicorn 之前先設定好日誌
    # 這樣 uvicorn 的啟動訊息也會被記錄下來
    setup_logging(log_filename=args.log_file)

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=settings.FASTAPI_PORT,
        log_level="info"
    )
