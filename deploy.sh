#!/bin/bash

cd /app

# 【磐石協議 v2.0：Colab 自動化測試與部署腳本】
# 本腳本將建立一個包含單元測試的完整應用，並在部署前執行品質檢查。
# 任何指令失敗都會立即中止腳本。
set -e

# --- [階段 1] 環境設定 ---
echo "✅ [1/4] 正在設定環境..."
pip install poetry > /dev/null 2>&1
export PATH="/root/.local/bin:$PATH"
echo "Poetry 已安裝並設定。"

# --- [階段 2] 安裝依賴 ---
echo "✅ [2/4] 正在使用 Poetry 安裝所有依賴 (包含開發工具)..."
(cd integrated_platform && poetry install --no-root > /dev/null 2>&1)
echo "依賴安裝完成。"

# --- [階段 3] 執行單元測試 (品質閘門) ---
echo "✅ [3/4] 正在執行品質檢查 (單元測試)..."
# 使用 -v (verbose) 模式顯示詳細測試結果
(cd integrated_platform && poetry run pytest -v)

echo "所有測試已通過！準備部署。"

# --- [階段 4] 啟動伺服器並產生網址 ---
echo "✅ [4/4] 正在啟動伺服器並產生公開網址..."
# 使用 nohup 確保伺服器在背景持續運行
(cd integrated_platform && poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &)
sleep 5 # 等待伺服器完全啟動

# 使用 Python 產生 Colab 的公開網址
python -c "from google.colab import output; print('\n\n--- 部署完成 ---'); output.serve_kernel_port_as_window(8000, anchor_text='點擊這裡，在新分頁中開啟您的應用程式')"

echo -e "\n如果連結未自動顯示，請檢查 Colab 輸出。腳本執行完畢。\n"
