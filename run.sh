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

# --- 步驟 3: 等待服務啟動並進行健康檢查 ---
# 從環境變數讀取埠號，如果未設定則使用預設值 8000
# 這樣可以確保腳本與 config.py 的設定同步
: "${UVICORN_PORT:=8000}"

echo "訊息：後端應用已嘗試啟動。等待服務完全就緒..."
# 根據作戰藍圖，增加等待時間以確保模型等耗時資源載入完成
sleep 15

# 使用新的 /health 端點進行更精確的健康檢查
# curl 的 -f 選項會在 HTTP 狀態碼為錯誤時 (如 503) 使 curl 以非零狀態碼退出
echo "正在對 http://localhost:${UVICORN_PORT}/health 進行健康檢查..."
if curl -fsS http://localhost:${UVICORN_PORT}/health > /dev/null; then
    echo "成功：後端服務已成功啟動並通過健康檢查！"
    echo "您現在可以透過 tail -f backend_startup.log 來監控即時日誌。"
else
    echo "錯誤：後端服務未通過健康檢查或未在預期埠號響應。"
    echo "--- 後端啟動日誌 (backend_startup.log) ---"
    cat backend_startup.log
    echo "----------------------------------------"
    exit 1
fi
