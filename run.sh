#!/bin/bash

# 【磐石協議 v6.0：沉默執行者部署腳本】
# 本腳本在執行時應完全靜默，所有狀態更新都透過日誌系統傳遞。

set -e

# --- 步驟 1: 自我定位 ---
# 使用 Python 和 pathlib 來取得專案根目錄，確保跨平台相容性
PROJECT_ROOT=$(python -c "from pathlib import Path; print(Path(__file__).resolve().parent)")

# --- 步驟 2: 環境準備 ---
# Poetry 會自動管理虛擬環境

# --- 步驟 3: 依賴安裝 ---
poetry install --no-root --with dev

# --- 步驟 4: 在背景啟動伺服器 ---
cd "$PROJECT_ROOT"
poetry run uvicorn integrated_platform.src.main:app --host 0.0.0.0 --port 8000
