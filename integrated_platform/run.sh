#!/bin/bash
# 啟動 uvicorn 伺服器
poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000
