# -*- coding: utf-8 -*-
"""
環境檢查模組 (EnvironmentChecker)

提供檢查系統資源（如磁碟空間、記憶體）的功能。
"""

import psutil

class EnvironmentError(Exception):
    """自訂環境錯誤異常"""
    pass

class EnvironmentChecker:
    """
    執行環境檢查的核心類別。
    """
    def __init__(self, config):
        self.config = config

    def check_disk_space(self):
        """
        檢查剩餘磁碟空間是否充足。
        """
        free_space_mb = psutil.disk_usage('/').free / (1024 * 1024)
        if free_space_mb < self.config.MIN_DISK_SPACE_MB:
            raise EnvironmentError(
                f"磁碟空間不足！剩餘 {free_space_mb:.2f} MB，"
                f"低於最低要求 {self.config.MIN_DISK_SPACE_MB} MB。"
            )
        print(f"磁碟空間檢查通過。剩餘 {free_space_mb:.2f} MB。")
        return True

    def check_memory(self):
        """
        檢查記憶體使用率是否在可接受範圍內。
        """
        memory_percent = psutil.virtual_memory().percent
        if memory_percent > self.config.MAX_MEMORY_USAGE_PERCENT:
            raise EnvironmentError(
                f"記憶體使用率過高！目前為 {memory_percent}%，"
                f"高於閾值 {self.config.MAX_MEMORY_USAGE_PERCENT}%。"
            )
        print(f"記憶體檢查通過。目前使用率 {memory_percent}%。")
        return True

    def run_all_checks(self):
        """
        執行所有環境檢查。
        """
        try:
            self.check_disk_space()
            self.check_memory()
            print("所有環境檢查均已通過。")
            return True
        except EnvironmentError as e:
            print(f"環境檢查失敗：{e}")
            # 在實際應用中，這裡應該呼叫日誌記錄器
            raise
