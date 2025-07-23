#!/bin/bash

# ==============================================================================
# 作戰藍圖 244-L: 鳳凰之心 - 環境感知與自我修復部署腳本
# 最高指導原則: 腳本必須像一個經驗豐富的工程師一樣思考和行動。
# ==============================================================================

# --- 通用設定 ---
# 當任何指令失敗時，立即終止腳本
set -e

# --- 格式化日誌函式 ---
# echof: Echo, Formatted
# $1: 階段名稱
# $2: 訊息
# $3: 顏色 (可選)
echof() {
    local phase=$1
    local message=$2
    local color=${3:-\e[32m} # 預設為綠色
    local nocolor='\033[0m'
    printf "${color}==> [Phase: %-25s] %s${nocolor}\n" "$phase" "$message"
}

# ==============================================================================
# Phase 0: 設定工作目錄
# ==============================================================================
echof "Setup" "正在設定工作目錄..."
cd "$(dirname "$0")"
echof "Setup" "工作目錄已設定為: $(pwd)"

# ==============================================================================
# Phase 1: 環境健全性檢查 (Sanity Check)
# ==============================================================================
echof "Sanity Check" "正在檢查核心工具 (python3, pip)..."
if ! command -v python3 &> /dev/null; then
    echof "Sanity Check" "錯誤: python3 未安裝。" "\e[31m"
    exit 1
fi
if ! command -v pip &> /dev/null; then
    echof "Sanity Check" "錯誤: pip 未安裝。" "\e[31m"
    exit 1
fi
echof "Sanity Check" "核心工具檢查通過。"

# ==============================================================================
# Phase 2: 依賴管理器設定 (Poetry)
# ==============================================================================
echof "Poetry Setup" "正在檢查並安裝 Poetry..."
if ! python3 -m poetry --version &> /dev/null; then
    echof "Poetry Setup" "Poetry 未安裝，正在透過 pip 安裝..."
    pip install poetry
    echof "Poetry Setup" "Poetry 已成功安裝。"
else
    echof "Poetry Setup" "Poetry 已安裝。"
fi

# ==============================================================================
# Phase 3: Colab 環境感知與配置
# ==============================================================================
echof "Environment Sensing" "正在偵測執行環境..."
if [ -n "$COLAB_GPU" ]; then
    echof "Environment Sensing" "偵測到 Colab 環境！正在使用環境變數強制 Poetry 使用系統 Python..." "\e[33m"
    export POETRY_VIRTUALENVS_CREATE=false
    echof "Environment Sensing" "環境變數 POETRY_VIRTUALENVS_CREATE 已設定為 false。" "\e[33m"
else
    echof "Environment Sensing" "未偵測到 Colab 環境，將使用預設的 Poetry 設定。"
fi

# ==============================================================================
# Phase 4: 安裝專案依賴
# ==============================================================================
echof "Dependency Install" "正在使用 Poetry 安裝專案依賴 (詳細模式)..."
# --no-ansi: 移除顏色代碼，讓日誌更乾淨
# --verbose: 提供最詳細的輸出，便於除錯
python3 -m poetry install --no-root --with dev --no-ansi --verbose
echof "Dependency Install" "專案依賴安裝完成。"

# ==============================================================================
# Phase 5: 啟動應用程式
# ==============================================================================
echof "Application Launch" "正在啟動後端應用程式..."
export PYTHONPATH=.
# 在 Colab 模式下，依賴已安裝到系統，故直接用系統 python 執行
# 這可以繞過 `poetry run` 可能引入的額外依賴解析問題
python3 -m integrated_platform.src.main > backend_startup.log 2>&1 &
echof "Application Launch" "應用程式已在背景啟動。"

# ==============================================================================
# Phase 6: 服務健康檢查 (強化版)
# ==============================================================================
# [作戰藍圖 244-V] 實施帶有重試機制的健康檢查循環
# --- 健康檢查設定 ---
: "${UVICORN_PORT:=8000}"
HEALTH_CHECK_URL="http://localhost:${UVICORN_PORT}/health"
MAX_ATTEMPTS=10 # 最大嘗試次數 (10 * 3s = 30s)
WAIT_SECONDS=3  # 每次嘗試間隔秒數
ATTEMPT_NUM=1

echof "Health Check" "啟動健康檢查程序，目標: ${HEALTH_CHECK_URL}"

while [ $ATTEMPT_NUM -le $MAX_ATTEMPTS ]; do
    echof "Health Check" "第 ${ATTEMPT_NUM}/${MAX_ATTEMPTS} 次嘗試連線..."
    # -f: 若伺服器錯誤則快速失敗 (不輸出 HTML 錯誤頁)
    # -sS: 靜默模式，但顯示錯誤
    if curl -fsS "${HEALTH_CHECK_URL}" > /dev/null; then
        echof "Mission Complete" "後端服務已成功啟動並通過健康檢查！" "\e[1;32m"
        echof "Mission Complete" "您現在可以透過 tail -f backend_startup.log 來監控即時日誌。" "\e[1;32m"
        exit 0 # 成功，正常退出腳本
    fi

    if [ $ATTEMPT_NUM -eq $MAX_ATTEMPTS ]; then
        echof "Health Check" "已達最大嘗試次數，服務啟動失敗。" "\e[31m"
        break # 跳出循環，執行失敗後的處理
    fi

    echof "Health Check" "服務尚未就緒，將在 ${WAIT_SECONDS} 秒後重試..." "\e[33m"
    sleep $WAIT_SECONDS
    ATTEMPT_NUM=$((ATTEMPT_NUM + 1))
done

# --- 若循環結束後仍未成功，則顯示錯誤並退出 ---
echof "Health Check" "錯誤: 後端服務未通過健康檢查或未在預期埠號響應。" "\e[31m"
echof "Health Check" "--- 後端啟動日誌 (backend_startup.log) ---" "\e[33m"
cat backend_startup.log
echof "Health Check" "----------------------------------------" "\e[33m"
exit 1
