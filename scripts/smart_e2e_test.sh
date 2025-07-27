#!/bin/bash

# ==============================================================================
#
# 作戰藍圖 275-E：鳳凰之心 v2.0 - 智能端到端測試腳本
#
# 核心目標：
# 1. 使用 uv 進行極速的依賴安裝。
# 2. 為每個測試階段建立完全隔離的 venv 環境。
# 3. 每個階段測試完成後，立即銷毀其 venv，釋放磁碟空間。
# 4. 支援 'mock' 和 'real' 模式，以應對不同測試場景。
#
# 語言契約：所有輸出與註解均需使用繁體中文。
#
# ==============================================================================

# --- 嚴格模式與全域設定 ---
set -euo pipefail
trap 'echo "💥 偵測到錯誤在行 $LINENO，指令為: $BASH_COMMAND" >&2' ERR

# --- 環境變數 (可由外部覆寫) ---
TEST_MODE="${TEST_MODE:-mock}"
PYTHON_EXEC="${PYTHON_EXEC:-python3}"

# --- 顏色代碼 ---
C_GREEN='\033[0;32m'
C_BLUE='\033[0;34m'
C_YELLOW='\033[1;33m'
C_RED='\033[0;31m'
C_NC='\033[0m' # No Color

# ==============================================================================
# 輔助函式庫
# ==============================================================================

log_info() { echo -e "${C_BLUE}ℹ [資訊] ${1}${C_NC}"; }
log_success() { echo -e "${C_GREEN}✅ [成功] ${1}${C_NC}"; }
log_warn() { echo -e "${C_YELLOW}⚠️ [警告] ${1}${C_NC}"; }
log_error() { echo -e "${C_RED}❌ [錯誤] ${1}${C_NC}" >&2; }

ensure_uv_installed() {
    log_info "正在檢查 'uv'..."
    if ! command -v uv &> /dev/null; then
        log_warn "'uv' 未找到，正在嘗試透過 pip 自動安裝..."
        if ! "${PYTHON_EXEC}" -m pip install uv; then
            log_error "無法自動安裝 'uv'。請手動安裝後再試。"
            exit 1
        fi
    fi
    log_success "'uv' 已準備就緒。版本: $(uv --version | grep -o '[0-9].*')"
}

# ==============================================================================
# 核心測試執行器
# ==============================================================================

# 函式：執行一個完整的測試階段
# 用法：run_test_stage "階段名稱" "venv目錄" "測試目標" "依賴文件1" "依賴文件2" ...
run_test_stage() {
    local stage_name="$1"
    local venv_dir="$2"
    local test_target="$3"
    shift 3
    local req_files=("$@")

    log_info "\n--- 階段：${stage_name} ---"

    # 檢查依賴文件是否存在
    for req_file in "${req_files[@]}"; do
        if [[ -n "$req_file" && ! -f "$req_file" ]]; then
            log_warn "依賴文件 '${req_file}' 不存在，跳過此測試階段。"
            return
        fi
    done

    # 使用 trap 來確保無論成功或失敗，都會執行清理
    trap "cleanup_venv '${venv_dir}'" RETURN

    log_info "為 '${stage_name}' 建立獨立環境 '${venv_dir}'..."
    uv venv "${venv_dir}" --python "${PYTHON_EXEC}"

    log_info "為 '${venv_dir}' 安裝依賴..."
    for req_file in "${req_files[@]}"; do
        if [[ -n "$req_file" ]]; then
             log_info "  -> 安裝 ${req_file}"
            uv pip install -r "${req_file}" --python="${venv_dir}/bin/python"
        fi
    done
    log_success "依賴安裝完成。"

    log_info "在 '${venv_dir}' 環境中執行 Pytest..."
    uv pip install pytest fastapi httpx --python="${venv_dir}/bin/python"
    "${venv_dir}/bin/python" -m pytest "${test_target}"
    log_success "Pytest 測試完成。"
}

cleanup_venv() {
    local venv_dir=$1
    log_info "正在清理並移除虛擬環境 '${venv_dir}'..."
    rm -rf "${venv_dir}"
    log_success "虛擬環境 '${venv_dir}' 已被徹底刪除。"
}


# ==============================================================================
# 主流程
# ==============================================================================

main() {
    log_info "====== 智能端到端測試啟動 (v2.0) ======"
    log_info "測試模式: ${TEST_MODE}"

    ensure_uv_installed

    # --- 階段一：核心 API 啟動測試 (無插件) ---
    run_test_stage "核心 API 啟動" ".venv_base" \
        "tests/ignition_test.py" \
        "requirements.txt" \
        "ALL_DATE/MP3_Converter_TXT/requirements/test.txt"

    # --- 階段二：量化分析插件獨立測試 ---
    run_test_stage "量化分析插件" ".venv_quant" \
        "apps/quant/tests/ignition_test.py" \
        "apps/quant/requirements.txt" \
        "ALL_DATE/MP3_Converter_TXT/requirements/test.txt"

    # --- 階段三：語音轉錄插件獨立測試 ---
    if [[ "$TEST_MODE" == "real" ]]; then
        log_info "模式：[真實測試]。將下載並測試大型語音模型。"
        run_test_stage "語音轉錄插件 (真實模式)" ".venv_transcriber" \
            "apps/transcriber/tests/test_e2e_flow.py" \
            "apps/transcriber/requirements.txt" \
            "ALL_DATE/MP3_Converter_TXT/requirements/test.txt"
    else
        log_info "模式：[模擬測試]。跳過大型依賴的真實測試。"
        # 在模擬模式下，我們可以只運行點火測試
        run_test_stage "語音轉錄插件 (模擬模式)" ".venv_transcriber_mock" \
            "apps/transcriber/tests/ignition_test.py" \
            "requirements.txt" \
            "ALL_DATE/MP3_Converter_TXT/requirements/test.txt"
    fi

    log_success "\n====== 所有測試階段均已成功完成 ======"
}

main "$@"
