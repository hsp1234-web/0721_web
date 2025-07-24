#!/bin/bash
#
# 作戰藍圖 v3.0.2 - Poetry + UV 整合測試 (移除 sudo)
#
set -e

echof() {
    local phase=$1
    local message=$2
    local color=${3:-\e[32m}
    local nocolor='\033[0m'
    printf "${color}==> [Phase: %-25s] %s${nocolor}\n" "$phase" "$message"
}

# --- 環境準備 ---
echof "Setup" "正在準備測試環境 (跳過 apt-get)..."

# --- 執行總指揮 ---
echof "Execution" "準備執行 v3.0.2 堡壘架構..."
export FASTAPI_PORT=8899
export LOG_DISPLAY_LINES=100
export PROJECT_FOLDER_NAME="WEB"

# 使用 poetry run 來確保在正確的虛擬環境中執行
poetry run python3 colab_test.py $FASTAPI_PORT &
START_PLATFORM_PID=$!
echof "Execution" "堡壘架構已在背景啟動 (PID: $START_PLATFORM_PID)。開始監控..."

# --- 監控與驗證 ---
WAIT_SECONDS=80
echof "Monitoring" "將在 ${WAIT_SECONDS} 秒後進行最終驗證..."
sleep $WAIT_SECONDS

# --- 驗證 ---
echof "Validation" "正在執行多維度驗證..."
HEALTH_CHECK_URL="http://localhost:${FASTAPI_PORT}/health"
HOME_PAGE_URL="http://localhost:${FASTAPI_PORT}/"
LOG_DB_PATH="logs.sqlite"
SUCCESS=true

# 1. 健康檢查
echof "Validation - Step 1" "執行健康檢查 (health)..."
if curl -fsS "${HEALTH_CHECK_URL}" > /dev/null; then
    echof "Validation - Step 1" "成功：健康檢查通過。" "\e[32m"
else
    echof "Validation - Step 1" "失敗：健康檢查未通過。" "\e[31m"
    SUCCESS=false
fi

# 2. 首頁內容驗證
echof "Validation - Step 2" "驗證首頁內容 (/) ..."
if curl -fsS "${HOME_PAGE_URL}" | grep -q "<title>整合型應用平台</title>"; then
    echof "Validation - Step 2" "成功：首頁內容符合預期。" "\e[32m"
else
    echof "Validation - Step 2" "失敗：首頁內容不符合預期。" "\e[31m"
    SUCCESS=false
fi

# 3. 核心資產驗證
echof "Validation - Step 3" "驗證核心日誌資料庫是否存在..."
if [ -f "$LOG_DB_PATH" ]; then
    echof "Validation - Step 3" "成功：日誌資料庫 '$LOG_DB_PATH' 已建立。" "\e[32m"
else
    echof "Validation - Step 3" "失敗：日誌資料庫 '$LOG_DB_PATH' 未找到。" "\e[31m"
    SUCCESS=false
fi

# --- 最終裁決 ---
if [ "$SUCCESS" = "true" ]; then
    echof "Validation" "✅ 所有驗證均已通過！" "\e[1;32m"
else
    echof "Validation" "❌ 部分驗證失敗，請檢查上述日誌。" "\e[1;31m"
    if command -v sqlite3 &> /dev/null; then
      echof "Diagnostics" "顯示 logs.sqlite 內容..."
      sqlite3 "$LOG_DB_PATH" "SELECT * FROM logs ORDER BY id DESC LIMIT 20;" || echo "無法讀取 '$LOG_DB_PATH'"
    else
      echof "Diagnostics" "sqlite3 未安裝，跳過日誌傾印。"
    fi
    kill $START_PLATFORM_PID || true
    exit 1
fi

# --- 清理 ---
echof "Cleanup" "測試成功，正在終止所有進程..."
kill $START_PLATFORM_PID
wait $START_PLATFORM_PID || true

rm -f logs.sqlite
rm -f STOP_SIGNAL
rm -f mock_colab.py
rm -f server.log

echof "Mission Complete" "高保真整合測試成功！" "\e[1;32m"
exit 0
