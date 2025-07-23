#!/bin/bash

# 【244-C 專案改善計畫：部署腳本】
# 旨在提供一個穩定且標準化的啟動程序。

# 當任何指令失敗時，立即終止腳本
set -e

# --- 步驟 1: 環境準備 ---
# 使用 Poetry 來確保所有依賴都已正確安裝。
# `--no-root` 避免安裝專案本身，`--with dev` 包含開發依賴。
echo "正在準備環境並安裝依賴..."
poetry install --no-root --with dev

# --- 步驟 2: 啟動應用程式 ---
# 透過 `poetry run` 確保在正確的虛擬環境中執行。
# 使用 `python -m src.main` 是官方推薦的模組化啟動方式，
# 這能讓 Python 解譯器正確設定路徑，避免 NameError。
echo "正在啟動應用程式..."
poetry run python -m integrated_platform.src.main
