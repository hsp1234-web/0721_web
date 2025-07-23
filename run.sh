#!/bin/bash
# v2.1.0 - 單線程堡壘架構 - 依賴安裝器
# 此腳本的唯一職責是安裝所有必要的 Python 套件。
set -e

# 一個簡單的日誌函式
echof() {
    local phase=$1
    local message=$2
    local color=${3:-\e[32m}
    local nocolor='\033[0m'
    printf "${color}==> [Phase: %-25s] %s${nocolor}\n" "$phase" "$message"
}

echof "Setup" "設定工作目錄..."
cd "$(dirname "$0")"

echof "Dependency Install" "使用 pip 安裝依賴 (from requirements.txt)..."
# 移除 --quiet 和 > /dev/null，以實現完全透明的日誌輸出
pip install -r requirements.txt

echof "Dependency Install" "專案依賴安裝完成。"
