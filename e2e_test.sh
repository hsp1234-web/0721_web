#!/bin/bash

# 嚴格模式
set -e

# --- 環境設定 ---
VENV_DIR=".e2e_venv"
HOST="127.0.0.1"
PORT="8000"
SERVER_LOG_FILE="WEB/e2e_server.log" # Log file will be inside WEB
PROJECT_DIR="WEB"

# --- 清理函式 ---
cleanup() {
    echo "--- 正在清理 ---"
    if ps -p $SERVER_PID > /dev/null; then
        echo "正在停止伺服器 (PID: $SERVER_PID)..."
        kill $SERVER_PID
        wait $SERVER_PID 2>/dev/null
    fi
    echo "正在移除虛擬環境..."
    rm -rf "$VENV_DIR"
    echo "正在移除日誌檔案..."
    rm -f "$SERVER_LOG_FILE"
    echo "清理完成。"
}

# --- 主程式 ---
trap cleanup EXIT

echo "--- 建立虛擬環境 ---"
python3 -m venv "$VENV_DIR"

echo "--- 啟用虛擬環境並安裝依賴 ---"
source "$VENV_DIR/bin/activate"
pip install -r "$PROJECT_DIR/requirements.txt"

echo "--- 在背景啟動核心服務 ---"
nohup python "$PROJECT_DIR/main.py" --host "$HOST" --port "$PORT" > "$SERVER_LOG_FILE" 2>&1 &
SERVER_PID=$!

echo "--- 等待 5 秒後驗證 API ---"
sleep 5

echo "--- 檢查日誌中是否有錯誤 ---"
if grep -i "error" "$SERVER_LOG_FILE"; then
    echo "💥 伺服器日誌中發現錯誤！"
    cat "$SERVER_LOG_FILE"
    exit 1
fi

echo "--- 測試根路徑 ---"
httpx get "http://$HOST:$PORT/"

echo "--- 測試成功 ---"
exit 0
