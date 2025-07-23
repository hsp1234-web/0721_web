#!/bin/bash
# 思路框架：所有開發相關的指令，都應透過 Poetry 執行，以確保環境一致性。

echo "--- 正在啟動 Poetry 環境中的測試套件 ---"
# 作法: 使用 `poetry run` 來執行測試指令。
#       Poetry 會自動啟用正確的虛擬環境，並找到已安裝的 pytest。
export PYTHONPATH=$PYTHONPATH:.
poetry run pytest
