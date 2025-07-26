#!/bin/bash

# ==============================================================================
#                 鳳凰之心專案：端到端 (E2E) 測試腳本
#
#   本腳本旨在提供一個標準化、可重複的流程，用於在一個純淨的環境中
#   驗證核心服務的穩定性與功能正確性。
#
#   執行流程：
#   1. 建立一個全新的、隔離的 Python 虛擬環境。
#   2. 僅安裝生產環境必要的依賴 (`base.txt`) 與測試工具 (`httpx`)。
#   3. 在後台啟動核心的 FastAPI 伺服器 (`server_main.py`)。
#   4. 透過 HTTP 請求，對所有關鍵 API 端點進行健康檢查與功能驗證。
#   5. 無論測試結果如何，確保在腳本結束時徹底關閉伺服器進程。
#   6. 根據測試結果，以清晰的狀態碼退出。
#
# ==============================================================================

# --- 通用設定 ---
set -e  # 如果任何命令失敗，立即退出
trap 'cleanup' EXIT  # 無論腳本如何退出（成功、失敗、中斷），都執行 cleanup 函式

# --- 變數定義 ---
VENV_DIR=".e2e_venv"
PYTHON_EXEC="$VENV_DIR/bin/python"
PIP_EXEC="$VENV_DIR/bin/pip"
SERVER_PID_FILE="server.pid"
SERVER_LOG_FILE="server.log"
HOST="127.0.0.1"
PORT=8002 # 使用一個與開發環境不同的埠號，避免衝突

# --- 函式定義 ---

# 清理函式：用於停止伺服器和移除臨時檔案
cleanup() {
    echo "--- 正在執行清理程序 ---"
    if [ -f "$SERVER_PID_FILE" ]; then
        SERVER_PID=$(cat "$SERVER_PID_FILE")
        echo "ℹ️  正在停止伺服器 (PID: $SERVER_PID)..."
        # 使用 kill 命令，並忽略 "No such process" 的錯誤
        kill "$SERVER_PID" 2>/dev/null || true
        # 等待一小段時間確保進程已關閉
        sleep 2
        # 如果進程還在，則強制 kill
        if ps -p "$SERVER_PID" > /dev/null; then
           echo "⚠️  伺服器未能溫和關閉，將強制結束。"
           kill -9 "$SERVER_PID" 2>/dev/null || true
        fi
        rm -f "$SERVER_PID_FILE"
        echo "✅ 伺服器已停止。"
    fi
    # 顯示日誌以供除錯
    if [ -f "$SERVER_LOG_FILE" ]; then
        echo "--- 伺服器日誌 ($SERVER_LOG_FILE) ---"
        cat "$SERVER_LOG_FILE"
        echo "------------------------------------"
        rm -f "$SERVER_LOG_FILE"
    fi
    echo "✅ 清理完成。"
}

# --- 測試主流程 ---

echo "=================================================="
echo "🚀 開始端到端 (E2E) 測試"
echo "=================================================="

# 1. 環境準備
echo "--- 步驟 1/5: 準備全新的虛擬環境 ---"
if [ -d "$VENV_DIR" ]; then
    echo "ℹ️  偵測到舊的 E2E 虛擬環境，正在移除..."
    rm -rf "$VENV_DIR"
fi
python3 -m venv "$VENV_DIR"
echo "✅ 虛擬環境已建立於 '$VENV_DIR'。"

# 2. 啟動虛擬環境並安裝依賴
echo "--- 步驟 2/5: 啟動虛擬環境並安裝依賴 ---"
source "$VENV_DIR/bin/activate"
echo "✅ 虛擬環境已啟動。"
# 首先安裝 uv 以加速
pip install uv > /dev/null
# 使用 uv 安裝所有開發依賴，確保一切可用
uv pip install -r requirements/dev.txt > /dev/null
echo "✅ 依賴安裝完成。"

# 3. 啟動核心服務
echo "--- 步驟 3/5: 在後台啟動核心伺服器 ---"
# 使用 nohup 在後台運行，並將日誌重定向
# 現在可以直接呼叫 python，因為 venv 已經啟動
nohup python server_main.py --host "$HOST" --port "$PORT" --no-reload > "$SERVER_LOG_FILE" 2>&1 &
# 獲取後台進程的 PID 並寫入檔案
SERVER_PID=$!
echo "$SERVER_PID" > "$SERVER_PID_FILE"
echo "✅ 伺服器已在後台啟動 (PID: $SERVER_PID)。正在等待其完全啟動..."
sleep 15 # 等待 15 秒，確保所有資源（包括懶加載的模型）都已準備就緒

# 4. 執行 API 測試
echo "--- 步驟 4/5: 執行 API 端點測試 ---"

# 測試 1: 根目錄 (/) - 基本健康檢查
echo "🧪 測試 1: GET / (基本健康檢查)"
httpx "http://$HOST:$PORT/" --timeout 10
echo "✅ 測試 1 通過。"

# 測試 2: /docs - API 文件
echo "🧪 測試 2: GET /docs (API 文件)"
httpx "http://$HOST:$PORT/docs" --timeout 10
echo "✅ 測試 2 通過。"

# 測試 3: /quant/data - 量化數據 API
echo "🧪 測試 3: GET /quant/data"
httpx "http://$HOST:$PORT/quant/data" --timeout 10
echo "✅ 測試 3 通過。"

# 測試 4: /transcriber/upload - 語音轉錄 API (首次呼叫，會觸發懶加載)
echo "🧪 測試 4: POST /transcriber/upload (首次呼叫，測試懶加載)"
# 我們使用專案根目錄的 fake_audio.mp3
# 第一次上傳，模型需要時間加載，所以 timeout 設定為 30 秒
response=$(httpx "http://$HOST:$PORT/transcriber/upload" --method POST --timeout 30 --files file fake_audio.mp3)
echo "✅ 測試 4 伺服器回應: $response"
# 簡單驗證回應是否包含檔名，以確認上傳成功
if [[ ! "$response" == *"fake_audio.mp3"* ]]; then
    echo "❌ 測試 4 失敗：回應中未找到預期的檔名 'fake_audio.mp3'。"
    exit 1
fi
echo "✅ 測試 4 通過。"


# 測試 5: /transcriber/upload - 語音轉錄 API (第二次呼叫，應使用快取)
echo "🧪 測試 5: POST /transcriber/upload (第二次呼叫，測試快取)"
# 第二次上傳，模型已加載，應在 10 秒內完成
response=$(httpx "http://$HOST:$PORT/transcriber/upload" --method POST --timeout 10 --files file fake_audio.mp3)
echo "✅ 測試 5 伺服器回應: $response"
# 簡單驗證回應是否包含檔名，以確認上傳成功
if [[ ! "$response" == *"fake_audio.mp3"* ]]; then
    echo "❌ 測試 5 失敗：回應中未找到預期的檔名 'fake_audio.mp3'。"
    exit 1
fi
echo "✅ 測試 5 通過。"

# 5. 測試完成
echo "--- 步驟 5/5: 所有測試均已成功通過 ---"

echo "=================================================="
echo "✅ 端到端 (E2E) 測試成功！"
echo "=================================================="

# 腳本會在這裡正常退出，並觸發 trap 'cleanup' EXIT
exit 0
