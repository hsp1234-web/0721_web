# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   核心檔案：logger/main.py (v2.0 升級版)                           ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       專案的「戰地記錄官」。負責處理所有日誌訊息，定義日誌的格式      ║
# ║       與顏色，並將其寫入後端的 .md 檔案中。                          ║
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       在完成其核心記錄任務的同時，它會將格式化後的日誌訊息，「抄送」  ║
# ║       一份給視覺指揮官 (PresentationManager)，由其決定是否以及如何   ║
# ║       顯示在畫面的滾動日誌層。實現了後端記錄與前端顯示的解耦。      ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

import logging
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import pytz
from datetime import datetime

class Logger:
    """
    專案的日誌記錄器，同時負責寫入檔案和更新畫面。
    """
    # ANSI 顏色代碼
    COLORS = {
        "INFO": "\033[97m",      # White
        "BATTLE": "\033[96m",    # Cyan
        "SUCCESS": "\033[92m",   # Green
        "WARNING": "\033[93m",   # Yellow
        "ERROR": "\033[91m",     # Red
        "CRITICAL": "\033[91;1m",# Bold Red
        "RESET": "\033[0m"       # Reset
    }

    def __init__(self, presentation_manager, log_dir="logs", timezone="Asia/Taipei"):
        self.pm = presentation_manager
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.timezone = pytz.timezone(timezone)

        # 自定義日誌級別
        logging.addLevelName(25, "BATTLE")
        logging.addLevelName(26, "SUCCESS")

        # 獲取 logger
        self.logger = logging.getLogger("PhoenixHeartLogger")
        self.logger.setLevel(logging.INFO)

        # 避免重複添加 handler
        if not self.logger.handlers:
            # 檔案 handler
            log_file = self.log_dir / f"日誌-{datetime.now(self.timezone).strftime('%Y-%m-%d')}.md"
            file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S'))
            self.logger.addHandler(file_handler)

    def _log(self, level, message, *args, **kwargs):
        """
        內部日誌處理函數。
        """
        # 格式化供檔案儲存的訊息
        log_func = getattr(self.logger, level.lower())
        log_func(message, *args, **kwargs)

        # 格式化供畫面顯示的訊息
        timestamp = datetime.now(self.timezone).strftime('%H:%M:%S.%f')[:-3]
        level_upper = level.upper()
        color = self.COLORS.get(level_upper, self.COLORS["INFO"])
        reset_color = self.COLORS["RESET"]

        display_message = f"[{timestamp}] {color}[{level_upper}]{reset_color} {message}"
        
        # 將格式化後的訊息抄送給視覺指揮官
        self.pm.add_log(display_message)

    # --- 對外介面 ---
    def info(self, message, *args, **kwargs):
        self._log("info", message, *args, **kwargs)

    def battle(self, message, *args, **kwargs):
        self._log("battle", message, *args, **kwargs)

    def success(self, message, *args, **kwargs):
        self._log("success", message, *args, **kwargs)

    def warning(self, message, *args, **kwargs):
        self._log("warning", message, *args, **kwargs)

    def error(self, message, *args, **kwargs):
        self._log("error", message, *args, **kwargs)

    def critical(self, message, *args, **kwargs):
        self._log("critical", message, *args, **kwargs)

