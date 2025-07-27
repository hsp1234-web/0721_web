# -*- coding: utf-8 -*-
"""
設定管理模組 (ConfigManager)

負責讀取、解析並提供應用程式的設定。
設定可以來自於檔案（如 config.ini, .env）或環境變數。
"""

class Config:
    """
    一個範例設定類別，之後可以擴充。
    """
    # 伺服器設定
    HOST = "127.0.0.1"
    PORT = 8080

    # 資源檢查設定
    MIN_DISK_SPACE_MB = 100  # 最小所需磁碟空間 (MB)
    MAX_MEMORY_USAGE_PERCENT = 90  # 最大可接受記憶體使用率 (%)

def get_config():
    """
    取得設定的工廠函式
    """
    return Config()
