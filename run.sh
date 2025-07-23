#!/bin/bash

# 【作戰藍圖 244-D：鳳凰之心 - 部署腳本】
# 目標：根除靜默錯誤，確保後端啟動過程透明且可追蹤。

# 當任何指令失敗時，立即終止腳本
set -e

# --- 步驟 1: 環境準備 ---
echo "正在準備環境並安裝依賴..."
poetry install --no-root --with dev

# --- 步驟 2: 啟動應用程式並捕獲輸出 ---
export PYTHONPATH=.
echo "正在啟動應用程式..."
# 將標準輸出與標準錯誤同時重定向到日誌檔和控制台
poetry run python -m integrated_platform.src.main > backend_startup.log 2>&1 &

# --- 步驟 3: 檢查應用啟動狀態 ---
# 等待一小段時間讓應用程式啟動
sleep 10

# 檢查日誌中是否有 FastAPI 的啟動成功訊息
if grep -q "Uvicorn running on" backend_startup.log; then
    echo "訊息：後端應用已成功啟動。"
else
    echo "錯誤：後端應用啟動失敗。請檢查 backend_startup.log 獲取詳細資訊。"
    cat backend_startup.log
    exit 1
fi

# --- 步驟 4: 服務健康檢查 ---
echo "正在進行服務健康檢查..."
if curl -s http://localhost:8000/docs > /dev/null; then
    echo "成功：後端服務已成功啟動並在 http://localhost:8000 響應！"
    echo "您現在可以透過 tail -f backend_startup.log 來監控即時日誌。"
else
    echo "警告：後端服務似乎未在預期埠號響應。請檢查 backend_startup.log 以獲取更多線索。"
    cat backend_startup.log
    exit 1
fi
