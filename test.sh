#!/bin/bash
# 腳本：test.sh - 基石契約模式 v2.4

export PYTHONPATH=.:./tests

# 啟動伺服器
poetry run uvicorn integrated_platform.src.main:app --host 0.0.0.0 --port 8000 &
SERVER_PID=$!

# 等待伺服器啟動
sleep 5

# 執行測試
poetry run pytest --timeout=60 -m "smoke or e2e"

# 停止伺服器
kill $SERVER_PID
