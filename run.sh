#!/bin/bash
# v3.0.2 - 整合智慧依賴管理器
set -e

# --- 視覺化函式 ---
print_header() {
    echo ""
    echo "===================================="
    echo "⚡️ $1"
    echo "===================================="
}

# --- 主要流程 ---
cd "$(dirname "$0")"

print_header "階段一：安裝核心工具"
if ! command -v pip &> /dev/null; then
    echo "pip 未找到，正在嘗試安裝 python3-pip..."
    sudo apt-get update && sudo apt-get install -y python3-pip
fi
pip install uv poetry --quiet
echo "- ✅ 核心工具 (UV & Poetry) 安裝完畢。"

print_header "階段二：執行智慧依賴分析"
echo "- 正在啟動 poetry_manager.py 來評估系統資源..."
# 執行智慧管理器，並將其最終生成的安裝指令儲存到一個變數中
INSTALL_COMMAND=$(python3 poetry_manager.py)
echo "- ✅ 依賴分析完成。"

print_header "階段三：執行安裝"
echo "$INSTALL_COMMAND" # 顯示將要執行的指令
# 執行由 poetry_manager.py 生成的指令
eval "$INSTALL_COMMAND"
echo "- ✅ 所有套件均已成功安裝到作戰環境中。"
