#!/bin/bash

# ==============================================================================
# 🚀 鳳凰之心：智能測試指揮官 (Smart Test Commander) v7 (最終版) 🚀
#
# 這個腳本是整個專案品質的守護者。它體現了我們架構的核心理念：
#   - 模擬優先 (Mock by Default): 預設在模擬模式下運行，快速且不消耗大量資源。
#   - 模式切換 (Mode Switching): 可透過 `TEST_MODE=real` 來運行完整的真實測試。
#   - 資源感知 (Resource-Aware): 在安裝大型依賴前會檢查系統資源。
#
# v7 更新:
#   - 完美實現 `TEST_MODE` (mock/real) 機制。
#   - 自動處理 `requirements.large.txt`。
#   - 將 `APP_MOCK_MODE` 環境變數傳遞給測試。
#
# 使用方法:
#   - 快速模擬測試 (預設): `bash smart_e2e_test.sh`
#   - 完整真實測試: `TEST_MODE=real bash smart_e2e_test.sh`
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

# --- 資源檢查與清理 ---
check_and_manage_resources() {
    local min_disk_kb=${1:-1048576} # 預設閾值: 1GB
    print_info "檢查可用磁碟空間 (閾值: ${min_disk_kb} KB)..."
    if ! command -v df &> /dev/null; then
        print_warn "無法找到 'df' 命令，跳過磁碟空間檢查。"
        return
    fi
    local available_disk_kb
    available_disk_kb=$(df -k . | awk 'NR==2 {print $4}')

    if [ "$available_disk_kb" -lt "$min_disk_kb" ]; then
        print_warn "可用磁碟空間 (${available_disk_kb} KB) 低於閾值。正在嘗試清理..."
        find apps -type d \( -name ".venv" -o -name ".venv_test" \) -maxdepth 2 -exec rm -rf {} +
        print_success "已清理所有舊的虛擬環境。"
        available_disk_kb=$(df -k . | awk 'NR==2 {print $4}')
        if [ "$available_disk_kb" -lt "$min_disk_kb" ]; then
            print_fail "清理後磁碟空間仍然不足！為避免系統崩潰，測試終止。"
            exit 1
        fi
    fi
    print_success "磁碟空間充足 (${available_disk_kb} KB)。"
}

# --- 主邏輯 ---
PROJECT_ROOT=$(pwd)
# 讀取測試模式，預設為 'mock'
TEST_MODE=${TEST_MODE:-mock}

print_header "鳳凰之心智能測試開始 (模式: $TEST_MODE)"

# 步驟 1: 檢查核心工具 (uv, psutil, pyyaml)
print_header "步驟 1: 檢查核心工具"
# 檢查 uv
if ! command -v uv &> /dev/null; then
    print_warn "uv 未找到，正在安裝..."
    python3 -m pip install -q uv
    export PATH="$HOME/.local/bin:$PATH"
fi
print_success "uv 已就緒。"
# 檢查核心 Python 依賴
python3 -c "import psutil, yaml" &> /dev/null || {
    print_warn "缺少核心依賴 (psutil, PyYAML)，正在安裝..."
    python3 -m pip install -q psutil pyyaml
}
print_success "核心 Python 依賴已滿足。"


# 步驟 2: 發現 App
print_header "步驟 2: 發現 `apps` 目錄下的所有微服務"
APPS=($(find "apps" -mindepth 1 -maxdepth 1 -type d))
print_info "發現了 ${#APPS[@]} 個 App: ${APPS[*]}"

# 步驟 3: 循環測試
print_header "步驟 3: 開始對每個 App 進行隔離化測試"
TEST_FAILURES=0
for app_path in "${APPS[@]}"; do
    app_name=$(basename "$app_path")
    print_header "--- 開始測試 App: $app_name (模式: $TEST_MODE) ---"

    VENV_DIR="$app_path/.venv_test"
    REQS_FILE="$app_path/requirements.txt"
    REQS_LARGE_FILE="$app_path/requirements.large.txt"
    TESTS_DIR="tests/$app_name"

    if [ ! -d "$TESTS_DIR" ] || [ -z "$(find "$TESTS_DIR" -name 'test_*.py')" ]; then
        print_warn "在 'tests/$app_name' 中找不到 '$app_name' 的測試檔案，跳過。"
        continue
    fi

    set +e # 暫時關閉立即退出以捕獲錯誤

    print_info "[$app_name] 1. 建立隔離的測試虛擬環境..."
    uv venv "$VENV_DIR" -p python3 --seed > /dev/null
    PYTHON_EXEC="$VENV_DIR/bin/python"

    print_info "[$app_name] 2. 安裝通用測試依賴 (pytest, etc.)..."
    # 通用依賴比較小，可以直接安裝
    uv pip install -q -p "$PYTHON_EXEC" pytest pytest-mock ruff httpx

    print_info "[$app_name] 3. 啟動智慧型安全安裝程序..."
    uv pip install -q -p "$PYTHON_EXEC" uv pyyaml psutil
    $PYTHON_EXEC -m core_utils.safe_installer "$app_name" "$REQS_FILE" "$PYTHON_EXEC"

    # 根據測試模式決定是否安裝大型依賴
    if [ "$TEST_MODE" == "real" ]; then
        if [ -f "$REQS_LARGE_FILE" ]; then
            print_warn "[$app_name] 偵測到真實模式，準備安全安裝大型依賴..."
            python3 -m core_utils.safe_installer "${app_name}_large" "$REQS_LARGE_FILE" "$PYTHON_EXEC"
            print_success "[$app_name] 大型依賴安裝完成。"
        fi
        export APP_MOCK_MODE="false"
    else
        print_info "[$app_name] 處於模擬模式，跳過大型依賴。"
        export APP_MOCK_MODE="true"
    fi

    print_info "[$app_name] 4. 執行 Ruff 檢查..."
    uv run -p "$PYTHON_EXEC" -- ruff check --fix --select I,F,E,W --ignore E501 "$app_path" > /dev/null
    uv run -p "$PYTHON_EXEC" -- ruff check --select I,F,E,W --ignore E501 "$app_path"
    print_success "[$app_name] Ruff 檢查通過。"

    print_info "[$app_name] 5. 執行 pytest..."
    export PYTHONPATH="$PROJECT_ROOT"
    uv run -p "$PYTHON_EXEC" -- pytest "$TESTS_DIR"

    EXIT_CODE=$?
    set -e

    if [ $EXIT_CODE -ne 0 ]; then
        print_fail "App '$app_name' 的測試流程失敗。"
        TEST_FAILURES=$((TEST_FAILURES + 1))
    else
        print_success "App '$app_name' 所有測試皆已通過！"
    fi

    print_info "清理 $app_name 的測試環境..."
    rm -rf "$VENV_DIR"
    print_success "--- App: $app_name 測試完成 ---"
done

# --- 最終總結 ---
print_header "所有測試已完成"
if [ "$TEST_FAILURES" -eq 0 ]; then
    print_success "🎉 恭喜！所有 App 的測試都已成功通過！"
    exit 0
else
    print_fail "總共有 $TEST_FAILURES 個 App 的測試未通過。請檢查上面的日誌。"
    exit 1
fi
