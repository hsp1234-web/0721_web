#!/bin/bash

# 【磐石協議 v6.0：沉默執行者部署腳本】
# 本腳本在執行時應完全靜默，所有狀態更新都透過日誌系統傳遞。

set -e

# --- 步驟 1: 自我定位 ---
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

# --- 步驟 2: 環境準備 ---
pip install poetry > /dev/null 2>&1
export PATH="/root/.local/bin:$PATH"

# --- 步驟 3: 依賴安裝 ---
(
  cd "$PROJECT_ROOT/integrated_platform"
  poetry install --no-root > /dev/null 2>&1
)

# --- 步驟 4: 在背景啟動伺服器 ---
cd "$PROJECT_ROOT/integrated_platform"
poetry run python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 > "$PROJECT_ROOT/server.log" 2>&1 &
