# -*- coding: utf-8 -*-
"""
日誌記錄模組 (Logger)
"""
import logging
import sys

def get_logger(name, level=logging.INFO):
    """
    建立並設定一個日誌記錄器。
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重複加入 handler
    if not logger.handlers:
        # 建立一個 handler，將日誌訊息輸出到標準輸出
        handler = logging.StreamHandler(sys.stdout)

        # 建立一個格式器，定義日誌訊息的格式
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)

        # 將 handler 加入到 logger
        logger.addHandler(handler)

    return logger

# 你也可以在這裡設定根日誌記錄器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
