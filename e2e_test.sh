#!/bin/bash

# 繁體中文: 端對端整合驗證腳本

# --- 設定 ---
# 設定 -e: 如果任何指令失敗，立即退出腳本
# 設定 -o pipefail: 如果管線中的任何指令失敗，整個管線的返回碼為失敗
set -eo pipefail

API_BASE_URL="http://127.0.0.1:8000"
APP_LOG="app_server.log"
# 清理舊的日誌檔案
rm -f $APP_LOG

# --- 輔助函式 ---
function print_header() {
    echo ""
    echo "======================================================================"
    echo "  $1"
    echo "======================================================================"
}

function cleanup() {
    print_header "清理程序"
    if [ ! -z "$SERVER_PID" ]; then
        echo "正在停止 API 伺服器 (PID: $SERVER_PID)..."
        # 使用 pkill 來確保所有子行程都被關閉
        pkill -P $SERVER_PID
        kill $SERVER_PID
        # 等待伺服器完全關閉
        sleep 2
    fi
    echo "清理完成。"
}

# --- 主邏輯 ---
# 設置 trap，確保在腳本退出時（無論成功或失敗）都會執行 cleanup 函式
trap cleanup EXIT

print_header "步驟 1: 安裝依賴套件"
if [ -f "requirements.txt" ]; then
    pip install --quiet -r requirements.txt
    echo "依賴套件已安裝。"
else
    echo "警告: 找不到 requirements.txt，跳過安裝步驟。"
fi

print_header "步驟 2: 在背景啟動主應用程式"

# 啟動應用程式並將輸出重新導向到日誌檔案
python main.py > $APP_LOG 2>&1 &
SERVER_PID=$!

# 等待幾秒鐘讓伺服器完全啟動
echo "等待伺服器啟動... (PID: $SERVER_PID)"
sleep 5

# 檢查伺服器是否仍在運行
if ! ps -p $SERVER_PID > /dev/null; then
    echo "錯誤: 伺服器啟動失敗！"
    echo "--- 應用程式日誌 ($APP_LOG) ---"
    cat $APP_LOG
    exit 1
fi
echo "伺服器已成功啟動。"

# --- 語音轉錄服務測試 ---
print_header "步驟 2: 測試語音轉錄服務"
# 檢查 fake_audio.mp3 是否存在
if [ ! -f "fake_audio.mp3" ]; then
    echo "錯誤: 找不到測試音檔 'fake_audio.mp3'。"
    exit 1
fi

echo "正在上傳測試音檔..."
UPLOAD_RESPONSE=$(curl -s -X POST -F "file=@fake_audio.mp3" "$API_BASE_URL/api/transcriber/upload")

if ! echo "$UPLOAD_RESPONSE" | grep -q "task_id"; then
    echo "錯誤: 上傳失敗！"
    echo "回應: $UPLOAD_RESPONSE"
    exit 1
fi

TASK_ID=$(echo "$UPLOAD_RESPONSE" | sed -n 's/.*"task_id":"\([^"]*\)".*/\1/p')
echo "音檔已上傳，任務 ID: $TASK_ID"

echo "正在輪詢任務狀態..."
for i in {1..30}; do
    STATUS_RESPONSE=$(curl -s "$API_BASE_URL/api/transcriber/status/$TASK_ID")
    TASK_STATUS=$(echo "$STATUS_RESPONSE" | sed -n 's/.*"status":"\([^"]*\)".*/\1/p')

    echo "  - 嘗試 $i/30: 目前狀態為 '$TASK_STATUS'"

    if [ "$TASK_STATUS" == "completed" ]; then
        RESULT_TEXT=$(echo "$STATUS_RESPONSE" | sed -n 's/.*"result_text":"\([^"]*\)".*/\1/p')
        if [ -z "$RESULT_TEXT" ]; then
            echo "錯誤: 任務已完成，但轉錄結果為空！"
            echo "完整回應: $STATUS_RESPONSE"
            exit 1
        fi
        echo "成功: 任務完成，轉錄結果: '$RESULT_TEXT'"
        break
    fi

    if [ "$i" -eq 30 ]; then
        echo "錯誤: 等待任務完成超時！"
        echo "最後狀態回應: $STATUS_RESPONSE"
        exit 1
    fi

    sleep 2
done

# --- 量化分析引擎測試 ---
print_header "步驟 3: 測試量化分析引擎"
# 建立一個模擬的資料庫給回測服務使用
echo "正在為量化分析建立模擬資料庫..."
python -c "import asyncio; from apps.quant.logic import main; asyncio.run(main())"

echo "正在發送回測請求..."
BACKTEST_PAYLOAD='{
    "target_asset": "AAPL",
    "factors": ["SMA_50", "RSI_14"],
    "weights": {"SMA_50": 0.6, "RSI_14": 0.4}
}'

BACKTEST_RESPONSE=$(curl -s -X POST -H "Content-Type: application/json" -d "$BACKTEST_PAYLOAD" "$API_BASE_URL/api/quant/backtest")

echo "回測 API 回應: $BACKTEST_RESPONSE"

# 驗證回應是否包含必要的績效欄位
if ! echo "$BACKTEST_RESPONSE" | grep -q "sharpe_ratio" || ! echo "$BACKTEST_RESPONSE" | grep -q "annualized_return"; then
    echo "錯誤: 回測回應中未包含必要的績效欄位！"
    exit 1
fi
echo "成功: 回測 API 運作正常，並返回了有效的績效數據。"

print_header "所有端對端測試已成功通過！"
exit 0
