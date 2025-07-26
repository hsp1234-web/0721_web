# -*- coding: utf-8 -*-
"""
一個獨立的、可重用的日誌設定模組。

此模組旨在提供一個標準化的方法來設定專案的日誌系統，
支援多種輸出格式 (如純文字和 Markdown)，並確保在整個應用程式中
日誌設定的一致性。

主要功能：
- setup_logger: 根據指定的設定，配置根日誌器。
- MarkdownFormatter: 一個自訂的日誌格式器，可將日誌格式化為 Markdown。
"""

import logging
import sys
from pathlib import Path

class MarkdownFormatter(logging.Formatter):
    """一個將日誌記錄格式化為 Markdown 的自訂格式器。"""

    FORMATS = {
        logging.DEBUG: "- **DEBUG**: {message}",
        logging.INFO: "- **INFO**: {message}",
        logging.WARNING: "### ⚠️ 系統警告\n- **WARN**: {message}",
        logging.ERROR: "### ❌ 嚴重錯誤\n- **ERROR**: {message}",
        logging.CRITICAL: "### 🔥 致命錯誤\n- **CRITICAL**: {message}"
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno, self._fmt)
        formatter = logging.Formatter(log_fmt, style='{')
        return formatter.format(record)

def setup_logger(log_dir: str = "logs", use_markdown: bool = False):
    """
    設定全域日誌器。

    Args:
        log_dir (str): 存放日誌檔案的資料夾名稱。
        use_markdown (bool): 如果為 True，日誌將以 Markdown 格式寫入 .md 檔案。
                             否則，將以純文字格式寫入 .log 檔案。
    """
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)

    # 根據 use_markdown 決定檔名和格式器
    if use_markdown:
        log_file = log_path / "system_log.md"
        formatter = MarkdownFormatter()
    else:
        log_file = log_path / "system_log.log"
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    # 取得根日誌器並設定等級
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除現有的處理器
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 檔案處理器
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    # 主控台處理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    root_logger.addHandler(console_handler)

    logging.info(f"日誌系統初始化完成，日誌將記錄於: {log_file}")
