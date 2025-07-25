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
print_header "步驟 1/6: 清理舊的虛擬環境"
if [ -d ".venv" ]; then
  print_info "偵測到舊的 '.venv' 目錄，正在將其移除..."
  rm -rf .venv
  print_success "舊環境已成功移除。"
else
  print_info "未發現舊的 '.venv' 目錄，無需清理。"
fi

# 2. 建立新的虛擬環境
print_header "步驟 2/6: 建立新的 Python 虛擬環境"
python3 -m venv .venv
print_success "虛擬環境 '.venv' 已成功建立。"

# 3. 啟動虛擬環境並安裝核心工具
print_header "步驟 3/6: 啟動環境並安裝 uv"
source .venv/bin/activate
pip install --upgrade pip > /dev/null
pip install uv > /dev/null
print_success "'uv' 已成功安裝到虛擬環境中。"

# 4. 使用 uv 同步依賴
print_header "步驟 4/6: 使用 uv 同步所有專案依賴"
print_info "正在同步 'requirements.txt'..."
uv pip sync requirements.txt
print_info "正在同步 'requirements/dev.txt'..."
# 為了處理 'dev.txt' 中的相對路徑 '-r base.txt'，我們需要切換目錄
(cd requirements && uv pip sync dev.txt)
print_success "所有依賴已成功同步。"

# 5. 執行 Ruff 程式碼品質檢查
print_header "步驟 5/6: 執行 Ruff 程式碼品質檢查"
print_info "正在安裝 'ruff'..."
uv pip install ruff > /dev/null
print_info "正在執行 'ruff check' (忽略風格錯誤)..."
# 我們只檢查，不修復。選擇性地忽略所有風格相關的規則 (E, W)
# 這裡我們示範性地只檢查最常見的問題，可以根據需求調整
ruff check . --select=F --ignore=E,W
print_success "Ruff 程式碼品質檢查完成，未發現重大錯誤。"

# 6. 執行最終的啟動導演腳本
print_header "步驟 6/6: 執行 'run.py' 進行最終視覺與功能驗證"
print_info "這將啟動引導伺服器並打開瀏覽器來展示啟動動畫。"
print_info "請觀察瀏覽器中的動畫是否符合預期。"
# 明確使用虛擬環境中的 python 來執行腳本，確保依賴正確
./.venv/bin/python run.py

print_header "測試流程已全部完成！"
print_success "如果瀏覽器中的啟動動畫正常顯示，則表示系統在全新環境下可成功部署與運行。"
