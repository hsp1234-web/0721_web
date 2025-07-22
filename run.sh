#!/bin/bash

# 獲取腳本所在的目錄
SCRIPT_DIR=$(cd $(dirname "$0") && pwd)

# 導航到專案根目錄 (integrated_platform)
cd "$SCRIPT_DIR/integrated_platform"

# 執行 poetry run uvicorn
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
