#!/bin/bash
#
# 鳳凰之心 - 統一測試執行腳本
#
# 此腳本是執行所有測試的單一入口點，包括單元、整合與端對端(E2E)測試。
#
# 執行流程:
# 1. 設定 shell，確保任何錯誤都會立即中止腳本。
# 2. 確定專案根目錄與虛擬環境路徑。
# 3. 呼叫智慧啟動器 `launch.py` 的 `--prepare-only` 模式，
#    以建立虛擬環境並安裝所有依賴 (包括測試專用依賴)。
# 4. 在背景啟動所有微服務。
# 5. 實施智慧等待機制，確認所有服務都已就緒。
# 6. 使用 Pytest 執行所有類型的測試。
# 7. 測試結束後，無論成功或失敗，都確保關閉所有背景服務。
#

# 若有任何命令失敗，立即退出
set -e

# --- 1. 路徑與環境設定 ---
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT="$SCRIPT_DIR/.."
VENV_PYTHON="$PROJECT_ROOT/.venvs/phoenix_heart/bin/python"
LAUNCH_SCRIPT="$PROJECT_ROOT/scripts/launch.py"

echo "=== 鳳凰之心 統一測試套件 ==="
echo "專案根目錄: $PROJECT_ROOT"
echo "虛擬環境 Python: $VENV_PYTHON"

# --- 2. 環境準備 ---
echo
echo "--- 步驟 1/5: 準備測試環境 (使用 launch.py --prepare-only) ---"
# 在 Colab 或 CI/CD 環境中，這會使用系統 Python
# 在本地開發中，這會建立並使用 .venvs/phoenix_heart/
# 我們需要找出 launch.py 會使用的 python 解釋器
if [ -f "$VENV_PYTHON" ]; then
    PYTHON_EXEC="$VENV_PYTHON"
else
    # 如果虛擬環境不存在，則 launch.py 會建立它或使用系統 python
    # 我們假設 launch.py 會處理好一切
    PYTHON_EXEC="python3"
fi
"$PYTHON_EXEC" "$LAUNCH_SCRIPT" --prepare-only

# 確定最終的 python 解釋器路徑
if [ -f "$VENV_PYTHON" ]; then
    PYTHON_EXEC="$VENV_PYTHON"
    echo "將使用虛擬環境中的 Python: $PYTHON_EXEC"
else
    PYTHON_EXEC=$(which python3)
    echo "將使用系統 Python: $PYTHON_EXEC"
fi


# --- 3. 在背景啟動服務 ---
echo
echo "--- 步驟 2/5: 在背景啟動微服務 ---"
# 將服務日誌導出，方便除錯
"$PYTHON_EXEC" "$LAUNCH_SCRIPT" > phoenix_services.log 2>&1 &
SERVER_PID=$!
echo "服務已啟動，主程序 PID: $SERVER_PID。日誌記錄於 phoenix_services.log"

# 定義一個函數，用於在腳本退出時自動清理背景程序
cleanup() {
    echo
    echo "--- 清理程序: 正在停止背景服務 (PID: $SERVER_PID) ---"
    # 使用 kill 命令來終止整個程序組
    # 這會將 SIGTERM 發送給 launch.py，由其內部的訊號處理器來優雅地關閉所有子服務
    kill $SERVER_PID
    # 等待一會兒確保程序退出
    sleep 2
    echo "✅ 清理完成。"
}

# 設定 trap，無論腳本是正常結束、出錯還是被中斷，都會執行 cleanup 函式
trap cleanup EXIT

# --- 4. 智慧等待服務就緒 ---
echo
echo "--- 步驟 3/5: 等待服務完全啟動 ---"
# 我們需要等待 quant (8001) 和 transcriber (8002) 服務
PORTS_TO_CHECK="8001 8002"
for port in $PORTS_TO_CHECK; do
    echo "正在檢查埠 $port..."
    # 使用 nc (netcat) 或 bash 的 /dev/tcp 來檢查埠是否開啟
    # timeout 命令限制等待時間為 30 秒
    if command -v nc &> /dev/null; then
        timeout 30 bash -c "until nc -z localhost $port; do sleep 1; done"
    else
        # 如果 nc 不可用，使用 bash 原生功能 (較不通用)
        timeout 30 bash -c "until (</dev/tcp/localhost/$port) &>/dev/null; do sleep 1; done"
    fi

    if [ $? -eq 0 ]; then
        echo "✅ 埠 $port 服務已就緒。"
    else
        echo "❌ 錯誤：等待埠 $port 服務超時！"
        echo "請檢查 phoenix_services.log 以了解詳細錯誤訊息。"
        exit 1
    fi
done
echo "所有服務均已成功啟動！"


# --- 5. 執行測試 ---
echo
echo "--- 步驟 4/5: 使用 Pytest 執行所有測試 ---"
# Pytest 會自動發現 `src` 目錄下所有 `test_*.py` 或 `*_test.py` 的檔案
"$PYTHON_EXEC" -m pytest "$PROJECT_ROOT/src/" "$PROJECT_ROOT/tests/"

# --- 6. 完成 ---
echo
echo "--- 步驟 5/5: 測試流程結束 ---"
echo "✅ 所有測試已成功完成。"
# trap 會在這裡觸發，自動執行 cleanup

exit 0
