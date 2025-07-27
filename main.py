# -*- coding: utf-8 -*-
"""
應用程式主進入點

負責初始化所有模組並啟動伺服器。
"""
import sys
from app.config import get_config
from app.environment import EnvironmentChecker, EnvironmentError
from app.server import APIServer
from app.utils.logger import get_logger

# 初始化日誌
logger = get_logger(__name__)

def main():
    """
    主函式
    """
    logger.info("正在啟動應用程式...")

    # 1. 載入設定
    try:
        config = get_config()
        logger.info("設定已成功載入。")
    except Exception as e:
        logger.error(f"無法載入設定檔：{e}", exc_info=True)
        sys.exit(1)

    # 2. 執行啟動前的環境檢查
    try:
        logger.info("正在執行啟動環境檢查...")
        env_checker = EnvironmentChecker(config)
        env_checker.run_all_checks()
        logger.info("環境檢查通過。")
    except EnvironmentError as e:
        logger.error(f"啟動檢查失敗，無法啟動伺服器：{e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"環境檢查時發生未預期的錯誤：{e}", exc_info=True)
        sys.exit(1)

    # 3. 初始化資料庫
    try:
        logger.info("正在初始化應用程式資料庫...")
        from app.db import initialize_database
        initialize_database()
        logger.info("資料庫初始化完成。")
    except Exception as e:
        logger.error(f"資料庫初始化時發生錯誤：{e}", exc_info=True)
        sys.exit(1)

    # 4. 初始化並啟動伺服器
    try:
        logger.info("正在初始化 API 伺服器...")
        server = APIServer(config, env_checker)
        logger.info(f"伺服器即將在 {config.HOST}:{config.PORT} 上啟動...")
        server.run()
    except Exception as e:
        logger.error(f"啟動伺服器時發生錯誤：{e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
