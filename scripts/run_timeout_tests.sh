#!/bin/bash

# 這個腳本用於測試 launch.py 的服務啟動超時機制

echo "🚀 開始執行超時測試..."

# 將 src 目錄添加到 PYTHONPATH 並執行 launch.py
export PYTHONPATH=$PYTHONPATH:$(pwd)/src && \
pip install -r requirements/base.txt && \
pip install Ipython && \
python scripts/launch.py > launch_output.log 2>&1 &
LAUNCH_PID=$!

echo "⏳ 等待 launch.py 執行 45 秒，以確保有足夠的時間觸發超時..."
sleep 45

# 殺掉 launch.py 進程
kill $LAUNCH_PID

echo "🔍 正在分析日誌輸出..."

# 檢查日誌中是否包含預期的成功和失敗訊息
if grep -q "✅ quant 服務健康檢查通過！" launch_output.log && \
   grep -q "❌ 錯誤: bad_service 服務在 30 秒內未啟動或健康檢查失敗。" launch_output.log && \
   grep -q "🛑 正在終止無回應的服務 bad_service" launch_output.log; then
    echo "✅ 測試通過！launch.py 成功處理了服務啟動超時。"
    rm launch_output.log
    # 清理創建的壞服務
    rm -rf src/bad_service
    rm -f requirements/bad_service.txt
    exit 0
else
    echo "🔴 測試失敗！launch.py 未能正確處理服務啟動超時。"
    echo "--- 日誌輸出 ---"
    cat launch_output.log
    echo "---"
    rm launch_output.log
    # 清理創建的壞服務
    rm -rf src/bad_service
    rm -f requirements/bad_service.txt
    exit 1
fi
