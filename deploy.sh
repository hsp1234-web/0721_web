#!/bin/bash

# 【磐石協議 v4.0：自我檢測部署腳本 (最終版)】
# 本腳本在執行前會進行一系列飛行前檢查，確保環境萬無一失。

# --- 核心戰術：設定在指令失敗時立即中止 ---
set -e

# --- 步驟 1: 自我定位 ---
# 無論從何處執行此腳本，都能精確找到其所在的專案根目錄。
echo "🚀 [1/5] 正在自動定位專案根目錄..."
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
echo "✅ 專案根目錄已鎖定: ${PROJECT_ROOT}"

# --- 步驟 2: 環境準備 (安裝核心工具) ---
echo "🚀 [2/5] 正在準備核心工具 (Poetry)..."
pip install poetry > /dev/null 2>&1
export PATH="/root/.local/bin:$PATH"
echo "✅ Poetry 工具已準備就緒。"

# --- 步驟 3: 飛行前檢查 (Pre-flight Check) ---
# 這是我們新的品質保證閘門。
echo "🚀 [3/5] 正在執行飛行前檢查..."

# 檢查 3.1: 確認 pyproject.toml 設計圖是否存在
echo "  - 正在檢查核心設計圖 (pyproject.toml)..."
if [ ! -f "$PROJECT_ROOT/pyproject.toml" ]; then
    echo "💥 [致命錯誤] 檢查失敗：在專案根目錄 '${PROJECT_ROOT}' 中找不到 'pyproject.toml' 檔案！"
    echo "   - 請確認檔案是否存在於您的 Git 倉庫中。"
    exit 1 # 中止執行
fi
echo "    ✅ 'pyproject.toml' 檔案已找到。"

# 檢查 3.2: 命令 Poetry 進行演習，檢查設計圖的有效性
echo "  - 正在命令 Poetry 驗證設計圖..."
# 使用子 Shell 確保 'poetry check' 在正確的目錄下執行
(cd "$PROJECT_ROOT" && poetry check)
echo "    ✅ Poetry 確認設計圖有效。"

echo "✅ 所有飛行前檢查已通過！"

# --- 步驟 4: 安裝專案依賴 ---
# 只有在所有檢查都通過後，才執行真正的安裝。
echo "🚀 [4/5] 正在安裝專案所有依賴..."
(cd "$PROJECT_ROOT" && poetry install --no-root)
echo "✅ 所有專案依賴已安裝完成。"

# --- 步驟 5: 移交指揮權給 Python ---
# 環境已完美就緒。喚醒 Python 腳本來執行應用程式的生命週期管理。
echo "🚀 [5/5] 環境準備完畢，正在移交指揮權給 Python 啟動器..."
echo "================================================================================"
(cd "$PROJECT_ROOT" && python colab_launch.py)
