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
  # 在啟動前，確保舊的日誌資料庫被清空，以便進行乾淨的驗證
  rm -f "$PROJECT_ROOT/logs.sqlite"
  cd "$PROJECT_ROOT/integrated_platform" && nohup poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 > ../server.log 2>&1 &
)
echo "✅ 伺服器啟動指令已發送。日誌將被寫入 'server.log' 和 'logs.sqlite'。"
echo "✅ 部署腳本任務完成。"
echo "================================================================================"
