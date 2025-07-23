#!/bin/bash

# 【磐石協議 v7.0：專業化執行腳本】
# 本腳本負責啟動後端伺服器。

set -e

# --- 步驟 1: 自我定位 ---
PROJECT_ROOT=$(pwd)

# --- 步驟 2: 在背景啟動伺服器 ---
cd "$PROJECT_ROOT"
poetry run uvicorn integrated_platform.src.main:app --host 0.0.0.0 --port 8000
