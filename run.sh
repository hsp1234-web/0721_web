#!/bin/bash
# v2.2.0 - 單線程堡壘架構 - 依賴安裝器 (含視覺化回饋)
# 此腳本的唯一職責是安裝所有必要的 Python 套件。
set -e

# --- 視覺化函式 ---
# 模擬進度條的函式
print_progress() {
    local total_width=50
    local percentage=$1
    local filled_width=$((percentage * total_width / 100))
    local empty_width=$((total_width - filled_width))
    local filled_chars=$(printf "%${filled_width}s" | tr ' ' '█')
    local empty_chars=$(printf "%${empty_width}s" | tr ' ' ' ')
    printf "\r[%s%s] %d%%" "$filled_chars" "$empty_chars" "$percentage"
}

# --- 主要流程 ---
cd "$(dirname "$0")"

echo "- 正在分析依賴列表 (requirements.txt)..."
sleep 1

# 模擬進度
for i in {0..100..2}; do
    print_progress $i
    sleep 0.01
done
echo "" # 換行

echo "- 開始下載並安裝套件..."
# 執行真正的安裝，但將其輸出重定向到 /dev/null 以避免干擾我們的進度條
# 我們仍然可以在出錯時看到錯誤訊息，因為 set -e 會讓腳本停止
pip install -r requirements.txt --quiet

echo "- 所有套件均已成功安裝到作戰環境中。"
