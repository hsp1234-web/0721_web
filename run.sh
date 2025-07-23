#!/bin/bash

# 【磐石協議 v6.0：沉默執行者部署腳本】
# 本腳本在執行時應完全靜默，所有狀態更新都透過日誌系統傳遞。

set -e

# --- 步驟 1: 自我定位 ---
# 修正：改用 'pwd' 指令取得目前路徑，確保執行穩定性
PROJECT_ROOT=$(pwd)

# --- 步驟 2: 環境準備 ---
# Poetry 會自動管理虛擬環境

# --- 步驟 3: 依賴安裝 ---
# 假設依賴已經透過 `poetry install` 安裝

# --- 步驟 4: 在背景啟動伺服器 ---
# 修正：直接使用虛擬環境的 Python 解譯器，繞過 poetry run
cd "$PROJECT_ROOT"
VENV_PATH=$(poetry env info --path)
"$VENV_PATH/bin/uvicorn" integrated_platform.src.main:app --host 0.0.0.0 --port 8000 &> server.log &
