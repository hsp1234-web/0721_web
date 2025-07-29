#!/bin/bash

# ==============================================================================
# 🚀 鳳凰之心：智能端對端 (E2E) 測試指揮官 v8 🚀
#
# 這個腳本是整個專案品質的最終守護者。它協調一個完整的端對端測試流程：
#   1. 啟動 (Launch): 在背景啟動所有微服務。
#   2. 等待 (Wait): 智慧地等待所有服務上線。
#   3. 測試 (Test): 執行 `pytest` 進行 API 層級的整合測試。
#   4. 關閉 (Shutdown): 乾淨地關閉所有背景服務，確保沒有任何程序殘留。
#
# 使用方法:
#   bash smart_e2e_test.sh
# ==============================================================================

set -e # 任何命令失敗時立即退出

# --- 顏色代碼 ---
C_HEADER="\033[95m"
C_CYAN="\033[96m"
C_GREEN="\033[92m"
C_WARN="\033[93m"
C_FAIL="\033[91m"
C_END="\033[0m"
C_BOLD="\033[1m"

# --- 輔助函式 ---
print_header() { echo -e "\n${C_HEADER}${C_BOLD}🚀 $1 🚀${C_END}"; }
print_success() { echo -e "${C_GREEN}✅ $1${C_END}"; }
print_info() { echo -e "${C_CYAN}ℹ️ $1${C_END}"; }
print_warn() { echo -e "${C_WARN}⚠️ $1${C_END}"; }
print_fail() { echo -e "${C_FAIL}❌ $1${C_END}"; }

# --- 清理函式 ---
cleanup() {
    print_header "執行清理程序"
    # 使用 pkill 和特有的啟動腳本名稱 `launch.py` 來確保只終止我們的服務
    # -f 選項會比對完整的命令列字串
    if pkill -f "launch.py"; then
        print_success "所有由 launch.py 啟動的服務已成功關閉。"
    else
        print_warn "沒有找到由 launch.py 啟動的程序，可能已經被關閉。"
    fi
}

# 註冊 trap，確保在腳本退出 (EXIT)、被中斷 (INT) 或終止 (TERM) 時都會執行 cleanup
trap cleanup EXIT INT TERM

# --- 主邏輯 ---
PROJECT_ROOT=$(pwd)

print_header "步驟 1: 準備主環境"
print_info "正在為 launch.py 安裝必要的依賴 (httpx)..."
uv pip install -q httpx
print_success "主環境準備就緒。"

print_header "步驟 2: 啟動所有微服務 (背景執行)"
# 使用 nohup 確保即使終端關閉，服務也能繼續運行，並將日誌輸出到檔案
nohup python3 launch.py > phoenix_e2e_test.log 2>&1 &
LAUNCHER_PID=$!
print_success "主啟動器已在背景啟動 (PID: $LAUNCHER_PID)。日誌請見 phoenix_e2e_test.log"

print_header "步驟 2: 等待所有服務上線"
# 假設我們的服務在 8000 (quant) 和 8001 (transcriber) 埠
# 這是根據 `proxy/proxy_config.json` 的預設值
ENDPOINTS=("http://localhost:8000/api/v1/quant/health" "http://localhost:8001/api/v1/transcriber/health")
MAX_WAIT=60
WAIT_INTERVAL=5
TIME_WAITED=0

for endpoint in "${ENDPOINTS[@]}"; do
    print_info "正在等待 $endpoint ..."
    while ! curl -s -f "$endpoint" > /dev/null; do
        if [ $TIME_WAITED -ge $MAX_WAIT ]; then
            print_fail "等待 $endpoint 超時 ($MAX_WAIT 秒)。請檢查日誌 phoenix_e2e_test.log"
            exit 1
        fi
        sleep $WAIT_INTERVAL
        TIME_WAITED=$((TIME_WAITED + WAIT_INTERVAL))
        echo -n "."
    done
    print_success "\n服務 $endpoint 已上線！"
done

print_header "步驟 3: 建立隔離的測試環境並執行 Pytest"
VENV_DIR=".venv_e2e_test"
PYTHON_EXEC="$VENV_DIR/bin/python"

print_info "建立隔離的 E2E 測試虛擬環境..."
uv venv "$VENV_DIR" -p python3 --seed > /dev/null

print_info "安裝測試依賴 (pytest, httpx)..."
uv pip install -q -p "$PYTHON_EXEC" pytest httpx

# 執行測試時，我們不需要再次安裝 `apps` 的依賴，因為服務已經在獨立環境中運行
# 我們只需要安裝能夠發送請求的客戶端即可
print_info "執行 Pytest 進行端對端測試..."
export PYTHONPATH="$PROJECT_ROOT"
# 我們假設測試檔案能夠從環境變數或預設值讀取到正確的 API 端點
set +e # 暫時關閉立即退出以捕獲測試失敗
uv run -p "$PYTHON_EXEC" -- pytest tests/
TEST_EXIT_CODE=$?
set -e

if [ $TEST_EXIT_CODE -ne 0 ]; then
    print_fail "端對端測試未通過 (退出碼: $TEST_EXIT_CODE)。"
    # 清理函式將會被 trap 自動呼叫
    exit 1
else
    print_success "🎉 所有端對端測試皆已通過！"
fi

print_header "測試流程已成功完成"
# 清理函式將會被 trap 自動呼叫
exit 0
