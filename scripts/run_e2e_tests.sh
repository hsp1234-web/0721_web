#!/bin/bash
#
# Phoenix Heart - Unified E2E Test Script v2.0
#
# This script is the single entry point for running all tests.
#
# Flow:
# 1. Ensure our shell exits immediately on any error.
# 2. Define a cleanup function to gracefully shut down services.
# 3. Find the project root directory.
# 4. Install all dependencies from the `requirements` directory.
# 5. Start all microservices in the background using `launch.py`.
# 6. Perform health checks with timeouts to ensure services are ready.
# 7. Run Pytest for unit/integration tests.
# 8. The cleanup function is called automatically on exit.
#

# Exit immediately on any error
set -e

# --- Cleanup Function ---
cleanup() {
    echo
    echo "--- 執行清理程序 ---"
    # pkill is more robust for finding and killing the process tree
    pkill -P $$ || true # Kill all child processes of this script
    echo "✅ 所有背景服務已關閉。"
}

# Register the cleanup function to be called on script exit
trap cleanup EXIT

# Get the script's directory and find the project root
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "=== 鳳凰之心整合測試套件 v2.0 ==="

# Step 1: Install dependencies
echo
echo "--- 步驟 1: 安裝所有依賴 ---"
python3 -m pip install -q -r "$PROJECT_ROOT/requirements/base.txt"
python3 -m pip install -q -r "$PROJECT_ROOT/requirements/quant.txt"
python3 -m pip install -q -r "$PROJECT_ROOT/requirements/transcriber.txt"
echo "✅ 依賴安裝完成。"

# Step 2: Start services in the background
echo
echo "--- 步驟 2: 在背景啟動服務 ---"
# Use a log file to capture server output for debugging
python3 "$PROJECT_ROOT/scripts/launch.py" > server.log 2>&1 &
# No need to capture PID, trap will handle cleanup

# Step 3: Health Checks
echo
echo "--- 步驟 3: 執行服務健康檢查 (最長等待 30 秒) ---"
SERVICES_TO_CHECK=(
    "http://localhost:8001"
    "http://localhost:8002"
)

for i in {1..15}; do
    all_ok=true
    for service_url in "${SERVICES_TO_CHECK[@]}"; do
        if ! curl -s -f -o /dev/null "$service_url"; then
            all_ok=false
            break
        fi
    done

    if [ "$all_ok" = true ]; then
        echo "✅ 所有服務均已啟動並回應正常！"
        break
    fi

    if [ "$i" -eq 15 ]; then
        echo "❌ 錯誤: 服務啟動超時。"
        echo "--- 伺服器日誌 (server.log) ---"
        cat server.log
        exit 1
    fi

    echo "等待服務啟動... (第 $i 次嘗試)"
    sleep 2
done

# Step 4: Run Pytest
echo
echo "--- 步驟 4: 執行 Pytest 測試 ---"
# Set PYTHONPATH to ensure tests can find the `src` modules
export PYTHONPATH="$PROJECT_ROOT"
python3 -m pytest "$PROJECT_ROOT/src/"

echo
echo "✅ 所有測試已成功完成。"
# The cleanup function will be called automatically here
