import logging
import sys
from pathlib import Path

# 建立一個自訂的 Markdown 格式器
class MarkdownFormatter(logging.Formatter):
    """一個將日誌記錄格式化為 Markdown 的自訂格式器。"""

    # 為不同等級的日誌定義 Markdown 格式
    FORMATS = {
        logging.DEBUG: "- **DEBUG**: {message}",
        logging.INFO: "- **INFO**: {message}",
        logging.WARNING: "### ⚠️ 系統警告\n- **WARN**: {message}",
        logging.ERROR: "### ❌ 嚴重錯誤\n- **ERROR**: {message}",
        logging.CRITICAL: "### 🔥 致命錯誤\n- **CRITICAL**: {message}"
    }

    def format(self, record):
        # 根據日誌等級選擇對應的格式
        log_fmt = self.FORMATS.get(record.levelno, self._fmt)
        formatter = logging.Formatter(log_fmt, style='{')
        return formatter.format(record)

def setup_markdown_logger(log_dir: Path, filename: str):
    """
    設定一個全域日誌器，將日誌以 Markdown 格式寫入指定檔案。

    Args:
        log_dir (Path): 存放日誌檔案的資料夾路徑。
        filename (str): 日誌檔案的名稱 (例如 'log-2025-07-26.md')。
    """
    log_dir.mkdir(exist_ok=True)
    log_file_path = log_dir / filename

    # 取得根日誌器，並設定最低記錄等級
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除任何可能已存在的舊處理器，確保日誌不會重複輸出
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # --- 檔案處理器：寫入到 .md 檔案 ---
    file_handler = logging.FileHandler(log_file_path, mode='w', encoding='utf-8')
    file_handler.setFormatter(MarkdownFormatter())
    root_logger.addHandler(file_handler)

    # --- 主控台處理器：同時在終端機顯示日誌 (可選，方便即時偵錯) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
    root_logger.addHandler(console_handler)

    # 寫入日誌檔案的標題
    with open(log_file_path, 'w', encoding='utf-8') as f:
        f.write(f"# 鳳凰之心作戰日誌 - {filename.replace('.md', '')}\n\n")
        f.write("## 系統啟動程序\n")

    logging.info(f"日誌系統初始化完成，日誌將記錄於: {log_file_path}")
