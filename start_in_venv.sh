#!/bin/bash

echo "--- [階段 1] 檢查並安裝 uv ---"
if ! command -v uv &> /dev/null
then
    echo "uv 未安裝，正在安裝..."
    python3 -m pip install uv
    if [ $? -ne 0 ]; then
        echo "錯誤：安裝 uv 失敗。"
    else
        echo "uv 已安裝完成。"
    fi
else
    echo "uv 已安裝。"
fi

echo "--- [階段 2] 建立或啟用虛擬環境 ---"
VENV_PATH="./.venv"
if [ ! -d "$VENV_PATH" ]; then
    echo "虛擬環境未找到，正在建立 $VENV_PATH..."
    python3 -m venv "$VENV_PATH"
    if [ $? -ne 0 ]; then
        echo "錯誤：建立虛擬環境失敗。"
    else
        echo "虛擬環境建立完成。"
    fi
else
    echo "虛擬環境已存在，將重新啟用。"
fi

echo "--- [階段 3] 啟用虛擬環境 ---"
source "$VENV_PATH/bin/activate"
echo "虛擬環境已啟用: $(which python)"

echo "--- [階段 4] 使用 uv 安裝專案依賴 ---"
if [ -f "requirements.txt" ]; then
    echo "偵測到 requirements.txt。正在使用 uv 安裝依賴..."
    uv pip install -r requirements.txt --system-site-packages
    if [ $? -ne 0 ]; then
        echo "錯誤：使用 uv 同步依賴失敗。"
    else
        echo "依賴安裝完成。"
    fi
else
    echo "錯誤：未找到 requirements.txt 檔案。請確保其存在於專案根目錄。"
fi

echo "--- [階段 5] 啟動後端服務 ---"
if [ -f "run.py" ]; then
    echo "正在啟動 run.py 後端服務..."
    exec python3 run.py
else
    echo "錯誤：未找到 run.py 檔案。請確保其存在於專案根目錄。"
fi
