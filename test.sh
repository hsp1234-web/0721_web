#!/bin/bash
# 【244-C 專案改善計畫：自動化測試腳本】
# 本腳本遵循「基石契約」模式，建立四道防線，確保專案品質。

echo "正在更新 lock 檔案以鎖定依賴版本..."
poetry lock
echo "正在安裝所有必要的依賴套件..."
poetry install --no-root --with dev

export PYTHONPATH=./integrated_platform

# --- 防線一：語法完整性檢查 (最快，< 1 秒) ---
# 確保所有程式碼的「語法」正確無誤，這是程式能被執行的最基本前提。
echo "正在執行 [1/4] 語法完整性檢查..."
poetry run ruff check . --select F,E7,E902,F821,F823,F401 --ignore D100,D101,D102,D103,D104,D105,D106,D107 || exit 1

# --- 防線二：依賴鏈完整性檢查 (次快，約 1-2 秒) ---
# 確保我們的依賴清單與實際需求完全一致，沒有遺漏或多餘。
echo "正在執行 [2/4] 依賴鏈完整性檢查..."
poetry run deptry . || exit 1

# --- 防線三：架構穩定性檢查 (點火測試) ---
# 確保系統的所有模組都能被正確載入，沒有結構性崩潰風險。
echo "正在執行 [3/4] 架構穩定性檢查..."
poetry run pytest --timeout=60 integrated_platform/tests/ignition_test.py || exit 1

# --- 防線四：核心業務邏輯檢查 (冒煙測試) ---
# 確保最關鍵的業務功能單元處於「可用」狀態。
echo "正在執行 [4/4] 核心業務邏輯檢查..."
poetry run pytest --timeout=60 -m smoke || exit 1

# 若所有防線均未被突破，則宣告契約達成
echo "所有檢查通過！專案品質符合預期標準。"
