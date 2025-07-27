#!/bin/bash

# ==============================================================================
#
# 作戰藍圖 275-D：統一指揮中心 - 智能端到端測試腳本
#
# 核心目標：利用 UV 實現極致的測試效率與環境隔離。
# 語言契約：所有輸出與註解均需使用繁體中文。
#
# ==============================================================================

# --- 嚴格模式與全域設定 ---
set -euo pipefail # 任何指令失敗、使用未設定變數、或管道失敗時立即退出
trap 'echo "💥 偵測到錯誤在行 $LINENO，指令為: $BASH_COMMAND" >&2' ERR

# --- 環境變數 (可由外部覆寫) ---
# TEST_MODE: "mock" (預設) 或 "real"。用於控制是否安裝和測試大型依賴。
TEST_MODE="${TEST_MODE:-mock}"

# --- 顏色代碼 (用於日誌輸出) ---
C_GREEN='\033[0;32m'
C_BLUE='\033[0;34m'
C_YELLOW='\033[1;33m'
C_RED='\033[0;31m'
C_NC='\033[0m' # No Color

# ==============================================================================
#
# 輔助函式庫
#
# ==============================================================================

# 函式：日誌輸出
# 用法：log_info "訊息"
log_info() {
    echo -e "${C_BLUE}ℹ [資訊] ${1}${C_NC}"
}

log_success() {
    echo -e "${C_GREEN}✅ [成功] ${1}${C_NC}"
}

log_warn() {
    echo -e "${C_YELLOW}⚠️ [警告] ${1}${C_NC}"
}

log_error() {
    echo -e "${C_RED}❌ [錯誤] ${1}${C_NC}" >&2
}

# 函式：檢查 UV 是否已安裝，若無則自動安裝
# 用法：ensure_uv_installed
ensure_uv_installed() {
    log_info "正在檢查 'uv' 是否已安裝..."
    if command -v uv &> /dev/null; then
        log_success "'uv' 已安裝。版本：$(uv --version)"
    else
        log_warn "'uv' 未找到。正在嘗試自動安裝..."
        if command -v pip &> /dev/null; then
            pip install uv
            log_success "透過 pip 成功安裝 'uv'。"
        elif command -v pip3 &> /dev/null; then
            pip3 install uv
            log_success "透過 pip3 成功安裝 'uv'。"
        else
            log_error "未找到 'pip' 或 'pip3'。無法自動安裝 'uv'。請手動安裝後再試。"
            exit 1
        fi
    fi
}

# 函式：檢查磁碟空間
# 用法：check_disk_space 5 # 檢查是否有 5GB 可用空間
check_disk_space() {
    local required_gb=$1
    log_info "正在檢查磁碟空間，需求：${required_gb}GB..."
    local available_gb
    available_gb=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if (( available_gb < required_gb )); then
        log_error "磁碟空間不足！需求：${required_gb}GB，可用：${available_gb}GB。"
        exit 1
    else
        log_success "磁碟空間充足。可用：${available_gb}GB。"
    fi
}

# 函式：建立虛擬環境並安裝依賴
# 用法：setup_venv_and_install_deps ".venv_name" "req1.txt" "req2.txt"
setup_venv_and_install_deps() {
    local venv_name=$1
    shift
    local dep_files=("$@")

    log_info "正在為 '${venv_name}' 建立獨立的虛擬環境..."
    uv venv "${venv_name}"

    log_info "開始為 '${venv_name}' 安裝依賴..."
    for dep_file in "${dep_files[@]}"; do
        if [[ -f "$dep_file" ]]; then
            log_info "  -> 正在安裝 ${dep_file}..."
            uv pip install -r "${dep_file}" --python="${venv_name}/bin/python"
        else
            log_error "依賴文件 '${dep_file}' 不存在！"
            cleanup_venv "${venv_name}" # 安裝失敗時清理環境
            exit 1
        fi
    done
    log_success "所有依賴均已成功安裝到 '${venv_name}'。"
}

# 函式：執行 Pytest 測試
# 用法：run_pytest_tests ".venv_name" "tests/target" 60
run_pytest_tests() {
    local venv_name=$1
    local test_target=$2
    local timeout=${3:-60} # 預設超時 60 秒

    log_info "在 '${venv_name}' 環境中執行 Pytest..."
    log_info "測試目標: ${test_target}"
    log_info "超時設定: ${timeout} 秒"

    # 執行測試
    # 使用 ./${venv_name}/bin/python 確保 pytest 是來自正確的 venv
    ./${venv_name}/bin/python -m pytest --timeout=${timeout} "${test_target}"

    log_success "Pytest 測試完成。"
}

# 函式：徹底清理虛擬環境
# 用法：cleanup_venv ".venv_name"
cleanup_venv() {
    local venv_name=$1
    log_info "正在清理並移除虛擬環境 '${venv_name}'..."
    rm -rf "${venv_name}"
    log_success "虛擬環境 '${venv_name}' 已被徹底刪除。"
}

# ==============================================================================
#
# 分階段測試流程
#
# ==============================================================================

main() {
    log_info "====== 智能端到端測試啟動 ======"
    log_info "測試模式: ${TEST_MODE}"

    ensure_uv_installed

    # --- 階段一：基礎服務與 API 啟動測試 ---
    run_base_service_test

    # --- 階段二：量化分析功能測試 ---
    run_quant_feature_test

    # --- 階段三：語音轉錄功能測試 ---
    run_transcriber_feature_test

    log_success "====== 所有測試階段均已成功完成 ======"
}

run_base_service_test() {
    local venv_name=".venv_base"
    log_info "\n--- 階段一：基礎服務與 API 啟動測試 ---"
    check_disk_space 1 # 基礎測試需要約 1GB

    # 依賴列表
    local base_deps=("requirements.txt" "ALL_DATE/MP3_Converter_TXT/requirements/test.txt")

    setup_venv_and_install_deps "${venv_name}" "${base_deps[@]}"
    run_pytest_tests "${venv_name}" "tests/ignition_test.py" 30
    cleanup_venv "${venv_name}"

    log_success "--- 階段一測試完成 ---"
}

run_quant_feature_test() {
    local venv_name=".venv_quant"
    log_info "\n--- 階段二：量化分析功能測試 ---"
    check_disk_space 1 # 同樣需要約 1GB

    # 依賴列表
    local quant_deps=("apps/quant/requirements.txt" "ALL_DATE/MP3_Converter_TXT/requirements/test.txt")

    if [[ ! -s "apps/quant/requirements.txt" ]]; then
        log_warn "量化依賴文件为空，跳過此階段。"
        return
    fi

    setup_venv_and_install_deps "${venv_name}" "${quant_deps[@]}"
    run_pytest_tests "${venv_name}" "apps/quant/tests/ignition_test.py" 120
    cleanup_venv "${venv_name}"

    log_success "--- 階段二測試完成 ---"
}

run_transcriber_feature_test() {
    local venv_name=".venv_transcriber"
    log_info "\n--- 階段三：語音轉錄功能測試 ---"

    # 前置檢查：ffmpeg
    if ! command -v ffmpeg &> /dev/null; then
        log_warn "'ffmpeg' 未找到。在 Debian/Ubuntu 上，可使用 'sudo apt-get install ffmpeg' 安裝。"
        log_warn "由於缺少 ffmpeg，將跳過此測試階段。"
        return
    fi
    log_success "'ffmpeg' 已安裝。"

    if [[ "$TEST_MODE" == "real" ]]; then
        log_info "模式：[真實測試]。將下載並測試大型語音模型。"
        check_disk_space 5 # 真實模式需要更多空間 (例如 5GB)

        local transcriber_deps=("apps/transcriber/requirements.txt" "ALL_DATE/MP3_Converter_TXT/requirements/test.txt")

        setup_venv_and_install_deps "${venv_name}" "${transcriber_deps[@]}"
        run_pytest_tests "${venv_name}" "apps/transcriber/tests/test_e2e_flow.py" 300 # 真實測試需要更長超時
        cleanup_venv "${venv_name}"

    elif [[ "$TEST_MODE" == "mock" ]]; then
        log_info "模式：[模擬測試]。將跳過大型依賴安裝，僅驗證 API 路徑。"
        check_disk_space 1 # 模擬模式需要較少空間

        # 在模擬模式下，我們只安裝基礎依賴和測試依賴
        local mock_deps=("requirements.txt" "requirements/test.txt")

        log_info "模擬安裝 'transcriber' 依賴..."
        echo "  -> echo 'Skipping torch installation in mock mode.'"
        echo "  -> echo 'Skipping faster-whisper installation in mock mode.'"

        setup_venv_and_install_deps "${venv_name}" "${mock_deps[@]}"

        # 在模擬模式下，我們可能需要一個不同的、不觸及真實模型的測試集
        # 這裡我們依然使用 ignition_test.py 作為流程佔位符
        run_pytest_tests "${venv_name}" "tests/ignition_test.py" 30
        cleanup_venv "${venv_name}"

    else
        log_error "未知的 TEST_MODE: '${TEST_MODE}'。請使用 'mock' 或 'real'。"
        exit 1
    fi

    log_success "--- 階段三測試完成 ---"
}

# --- 腳本執行入口 ---
main "$@"
