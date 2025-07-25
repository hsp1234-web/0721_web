#!/bin/bash

# --- 標準化的鳳凰之心引擎啟動腳本 ---

# 設置顏色以便輸出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VENV_DIR=".venv"

echo -e "${YELLOW}=== 鳳凰之心引擎啟動程序 ===${NC}"

# 步驟 1: 檢查並創建虛擬環境
if [ ! -d "$VENV_DIR" ]; then
    echo "-> 虛擬環境不存在，正在創建於 '$VENV_DIR'..."
    python3 -m venv $VENV_DIR
    if [ $? -ne 0 ]; then
        echo "錯誤：無法創建虛擬環境。請確保 'python3' 和 'venv' 模組已安裝。"
        exit 1
    fi
else
    echo "-> 虛擬環境已存在。"
fi

# 步驟 2: 激活虛擬環境並安裝/更新依賴
echo -e "\n${YELLOW}--- 正在安裝/更新依賴... ---${NC}"
source $VENV_DIR/bin/activate
pip install -r requirements.txt --upgrade
if [ $? -ne 0 ]; then
    echo "錯誤：依賴安裝失敗。"
    deactivate
    exit 1
fi
echo -e "${GREEN}✅ 依賴已是最新狀態。${NC}"

# 步驟 3: 啟動 Uvicorn 伺服器
echo -e "\n${YELLOW}--- 正在啟動後端引擎... ---${NC}"
echo "日誌將會輸出到此終端機。使用 Ctrl+C 來關閉伺服器。"

# 使用 uvicorn 啟動，並傳遞 --reload 參數以方便開發
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 停用虛擬環境
deactivate
echo -e "\n${YELLOW}=== 鳳凰之心引擎已關閉 ===${NC}"
