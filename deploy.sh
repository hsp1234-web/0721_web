#!/bin/bash

# 【磐石協議 v5.0：職責回歸部署腳本 (最終版)】
# 本腳本只負責準備環境與在背景啟動伺服器。

set -e

# --- 步驟 1: 自我定位 ---
echo "🚀 [1/4] 正在自動定位專案根目錄..."
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "✅ 專案根目錄已鎖定: ${PROJECT_ROOT}"

# --- 步驟 2: 環境準備 ---
echo "🚀 [2/4] 正在準備核心工具 (Poetry)..."
pip install poetry > /dev/null 2>&1
export PATH="/root/.local/bin:$PATH"
echo "✅ Poetry 工具已準備就緒。"

# --- 步驟 3: 飛行前檢查與依賴安裝 ---
echo "🚀 [3/4] 正在執行飛行前檢查與依賴安裝..."
# 將所有需要切換目錄的操作，都放在一個子 Shell 中執行，確保萬無一失
(
  cd "$PROJECT_ROOT"
  echo "  - 正在檢查核心設計圖 (pyproject.toml)..."
  if [ ! -f "integrated_platform/pyproject.toml" ]; then
    echo "💥 [致命錯誤] 檢查失敗：找不到 'pyproject.toml' 檔案！"
    exit 1
  fi
  echo "    ✅ 'pyproject.toml' 檔案已找到。"
  (cd integrated_platform && poetry check)
  echo "    ✅ Poetry 確認設計圖有效。"
  echo "  - 正在安裝專案所有依賴..."
  (cd integrated_platform && poetry install --no-root)
)
echo "✅ 所有專案依賴已安裝完成。"

# --- 步驟 4: 在背景啟動伺服器並退出 ---
# 這是最關鍵的改變：我們只負責啟動，然後立刻功成身退。
# 將日誌導向 server.log，並使用 nohup 確保其持續運行。
echo "🚀 [4/4] 正在背景啟動 FastAPI 伺服器..."
(
  cd "$PROJECT_ROOT/integrated_platform" && nohup poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 > ../server.log 2>&1 &
)
echo "✅ 伺服器啟動指令已發送。"
echo "🚀 [5/5] 正在生成最終日誌報告..."

# 假設日誌資料庫名稱為 logs.sqlite
DB_PATH="logs.sqlite"

# 檢查日誌資料庫是否存在
if [ ! -f "integrated_platform/$DB_PATH" ]; then
    echo "🟡 警告: 找不到日誌資料庫 '$DB_PATH'。將建立一個空的資料庫作為範例。"
    # 使用 Python 建立一個帶有範例日誌的資料庫
    (
        cd "$PROJECT_ROOT/integrated_platform" && poetry run python -c "
from pathlib import Path
import sys
sys.path.append('src')
from log_manager import LogManager
db_path = Path('$DB_PATH')
if db_path.exists():
    db_path.unlink()
log_manager = LogManager(db_path)
log_manager.log('INFO', '部署腳本自動生成的範例日誌。')
log_manager.log('WARNING', '伺服器已啟動。')
log_manager.close()
"
    )
fi

(
    cd "$PROJECT_ROOT/integrated_platform" && poetry run python generate_log_report.py "$DB_PATH"
)
echo "✅ 最終日誌報告已生成，本腳本任務完成。"
echo "================================================================================"
