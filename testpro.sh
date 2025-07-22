#!/bin/bash
# 腳本：testpro.sh - 全系統實彈演習

# --- 階段一：環境驗證 ---
echo "正在驗證 Python 環境..."
(cd integrated_platform && poetry run python verify_imports.py)
VERIFICATION_EXIT_CODE=$?
if [ $VERIFICATION_EXIT_CODE -ne 0 ]; then
    echo "環境驗證失敗，請檢查依賴項。"
    exit $VERIFICATION_EXIT_CODE
fi
echo "環境驗證成功。"

# --- 階段二：啟動真實戰場 ---
echo "正在安裝依賴項..."
(cd integrated_platform && poetry lock && poetry install)
echo "正在啟動真實作戰伺服器..."
export PATH="/root/.local/bin:$PATH"
export WHISPER_MODEL_SIZE="tiny"
bash run.sh &
SERVER_PID=$!
echo "伺服器已在背景啟動，PID: $SERVER_PID"

# 給伺服器一些時間來完全啟動
sleep 60

# --- 階段三：執行實彈攻擊 ---
echo "正在對線上伺服器，執行端對端實彈測試..."
# 進入正確的目錄以執行 pytest
cd integrated_platform || exit 1
# 執行我們全新的 E2E 測試套件
poetry run pytest tests/e2e/test_full_system_flow.py
TEST_EXIT_CODE=$?

# --- 階段四：確保戰場清理 ---
echo "正在關閉作戰伺服器，清理戰場..."
kill $SERVER_PID
echo "伺服器進程 (PID: $SERVER_PID) 已被終止。"

# 根據測試結果返回退出碼
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "演習成功！"
    exit 0
else
    echo "演習失敗！"
    exit $TEST_EXIT_CODE
fi
