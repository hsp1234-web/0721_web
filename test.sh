#!/bin/bash
# 最終作戰計畫 P8：鳳凰之心
# 階段一：環境基礎重塑
# 此腳本負責在 Poetry 管理的虛擬環境中執行 pytest 測試套件。

echo "🔵 [資訊] 正在啟動 Poetry 環境中的測試套件..."

# 設定 PYTHONPATH 以確保專案根目錄下的模組能被正確找到。
export PYTHONPATH=$PYTHONPATH:.

# 使用 `poetry run` 來執行測試指令。
# Poetry 會自動啟用正確的虛擬環境，並找到已安裝的 pytest。
if ! poetry run pytest; then
    echo "🔴 [錯誤] 測試執行失敗。"
    exit 1
fi

echo "✅ [成功] 所有測試均已通過。"
