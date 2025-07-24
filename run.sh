#!/bin/bash
# 最終作戰計畫 P8：鳳凰之心
# 階段一：環境基礎重塑
# 此腳本負責以 Poetry + uv 為核心，建立一個現代化的、可重現的、極速的 Python 環境。

# --- 安全第一：確保在正確的目錄執行 ---
# cd "$(dirname "$0")" || exit 1

# --- 訊息輸出美學 ---
echo_info() {
    echo "🔵 [資訊] $1"
}
echo_success() {
    echo "✅ [成功] $1"
}
echo_warning() {
    echo "🟠 [警告] $1"
}
echo_error() {
    echo "🔴 [錯誤] $1"
    exit 1
}

# --- 步驟一：升級核心工具 ---
echo_info "正在確保 pip 是最新版本..."
python3 -m pip install --upgrade pip &> /dev/null || echo_warning "無法升級 pip，將使用現有版本。"

# --- 步驟二：安裝 Poetry 與 uv ---
echo_info "正在安裝核心管理工具 (Poetry) 與加速器 (uv)..."
if ! python3 -m pip install poetry uv; then
    echo_error "安裝 Poetry 或 uv 失敗。部署中止。"
fi
echo_success "Poetry 與 uv 已成功安裝。"

# --- 步驟三：配置 Poetry 使用 uv ---
echo_info "正在配置 Poetry 使用 uv 作為其渦輪增壓引擎..."
if ! poetry config installer.plugin uv; then
    echo_warning "配置 Poetry 的 uv 插件失敗。可能已配置或 Poetry 版本不支援。"
fi
echo_info "正在配置 Poetry 將虛擬環境置於專案目錄內 (.venv)..."
if ! poetry config virtualenvs.in-project true; then
    echo_warning "配置 Poetry 的 in-project virtualenv 失敗。"
fi
echo_success "Poetry 加速器配置完成。"

# --- 步驟四：執行極速依賴安裝 ---
echo_info "正在使用 Poetry + uv 組合進行極速依賴安裝..."
if ! poetry install --no-root; then
    echo_error "使用 'poetry install' 進行依賴安裝時發生嚴重錯誤。"
fi
echo_success "環境部署成功完成！所有依賴均已透過 Poetry + uv 安裝在 .venv 中。"

# --- 最終提示 ---
echo_info "若要啟動應用程式，請執行：poetry run python core_run.py"
echo_info "若要執行測試，請執行：bash test.sh"
