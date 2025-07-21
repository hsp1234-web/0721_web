# generate_log_report.py

import argparse
from pathlib import Path
import sys

# 將 src 目錄添加到系統路徑中，以便導入模組
sys.path.append(str(Path(__file__).parent.joinpath('src')))

from archiver import generate_final_log_file

def main():
    """
    主執行函數：解析命令列參數並生成日誌報告。
    """
    parser = argparse.ArgumentParser(description="從資料庫生成最終日誌報告。")
    parser.add_argument(
        "db_path",
        type=Path,
        help="SQLite 資料庫檔案的路徑 (例如：logs.sqlite)。"
    )
    args = parser.parse_args()

    # 檢查資料庫檔案是否存在
    if not args.db_path.is_file():
        print(f"錯誤：找不到指定的資料庫檔案 '{args.db_path}'。")
        sys.exit(1)

    # 生成最終日誌檔案
    generate_final_log_file(args.db_path)

if __name__ == "__main__":
    main()
