#!/bin/bash
#
# 鳳凰之心 - 統一整合測試腳本
#
# 這個腳本是執行所有測試的唯一入口點。
#
# 流程:
# 1. 確保我們的 shell 在遇到錯誤時會立即退出。
# 2. 找到專案的根目錄。
# 3. 呼叫智慧啟動器 `launch.py` 的 `--prepare-only` 模式，
#    這會建立虛擬環境並安裝所有依賴，然後乾淨地退出。
# 4. 啟動 `pytest` 來執行 `src/` 目錄下的所有測試。
#

# 在遇到任何錯誤時立即退出
set -e

# 獲取腳本所在的目錄，並找到專案根目錄
SCRIPT_DIR=$(dirname "$(readlink -f "$0")")
PROJECT_ROOT="$SCRIPT_DIR/.."

echo "=== 鳳凰之心整合測試 ==="

# 步驟 1: 準備測試環境
echo
echo "--- 準備環境 (使用 launch.py --prepare-only) ---"
python3 "$PROJECT_ROOT/scripts/launch.py" --prepare-only

# 步驟 2: 執行 Pytest
echo
echo "--- 執行測試 (使用 pytest) ---"
VENV_PYTHON="$PROJECT_ROOT/.venvs/base/bin/python"
"$VENV_PYTHON" -m pytest "$PROJECT_ROOT/src/"

echo
echo "✅ 所有測試已成功完成。"
