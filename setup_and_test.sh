#!/bin/bash

# 啟用 -e 選項，讓腳本在任何指令失敗時立即退出
set -e

# --- 輔助函式 ---
print_header() {
  echo ""
  echo "======================================================================"
  echo "🚀 $1"
  echo "======================================================================"
}

print_info() {
  echo "ℹ️  $1"
}

print_success() {
  echo "✅ $1"
}

# --- 主要邏輯 ---

# 1. 清理舊環境
print_header "步驟 1/7: 清理舊的虛擬環境"
if [ -d ".venv" ]; then
  print_info "偵測到舊的 '.venv' 目錄，正在將其移除..."
  rm -rf .venv
  print_success "舊環境已成功移除。"
else
  print_info "未發現舊的 '.venv' 目錄，無需清理。"
fi

# 2. 建立新的虛擬環境
print_header "步驟 2/7: 建立新的 Python 虛擬環境"
python3 -m venv .venv
print_success "虛擬環境 '.venv' 已成功建立。"

# 3. 啟動虛擬環境並安裝核心工具
print_header "步驟 3/7: 啟動環境並安裝核心工具"
source .venv/bin/activate
pip install --upgrade pip > /dev/null
pip install uv > /dev/null
print_success "'uv' 已成功安裝到虛擬環境中。"

# 4. 使用 pip 安裝依賴
print_header "步驟 4/7: 使用 pip 安裝所有專案依賴"
print_info "正在安裝開發環境依賴 (包含核心依賴)..."
pip install -r requirements/dev.txt
print_success "所有依賴已成功安裝。"

# 5. 執行程式碼品質與依賴檢查
print_header "步驟 5/7: 執行程式碼品質與依賴檢查"
print_info "正在安裝檢查工具 (Ruff, deptry)..."
# ruff 和 deptry 都在 dev.txt 中，已經被安裝
print_info "正在執行 'ruff check'..."
ruff check . --select=F --ignore=E,W
print_success "Ruff 程式碼品質檢查完成。"
print_info "正在執行 'deptry' 依賴關係檢查..."
deptry .
print_success "Deptry 依賴關係檢查完成。"


# 6. 執行最終的啟動導演腳本
print_header "步驟 6/7: 執行 'run.py' 進行最終視覺與功能驗證"
print_info "這將啟動引導伺服器並打開瀏覽器來展示啟動動畫。"
print_info "請觀察瀏覽器中的動畫是否符合預期。"
# 明確使用虛擬環境中的 python 來執行腳本，確保依賴正確
./.venv/bin/python run.py

print_header "步驟 7/7: 測試流程已全部完成！"
print_success "如果瀏覽器中的啟動動畫正常顯示，則表示系統在全新環境下可成功部署與運行。"
