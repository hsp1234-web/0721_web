# 繁體中文: apps/quant/logic.py - 量化分析核心邏輯封裝

import asyncio
from pathlib import Path
from typing import Any, Dict

# 調整導入路徑以適應新的模組結構
from .core.db.db_manager import DBManager
from .models.strategy_models import Strategy, PerformanceReport
from .services.backtesting_service import BacktestingService

# 假設資料庫檔案位於 `apps/quant/data/` 目錄下
# 在真實應用中，路徑管理會更完善
DB_PATH = Path(__file__).parent / "data" / "prometheus.duckdb"
DB_MANAGER = DBManager(db_path=str(DB_PATH))

async def run_backtest(strategy_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    接收一個策略字典，執行回測，並返回績效報告。

    Args:
        strategy_dict (Dict[str, Any]): 一個包含策略定義的字典，
                                         例如:
                                         {
                                             "target_asset": "AAPL",
                                             "factors": ["SMA_50", "RSI_14"],
                                             "weights": {"SMA_50": 0.7, "RSI_14": 0.3}
                                         }

    Returns:
        Dict[str, Any]: 一個包含績效報告的字典。
    """
    try:
        # 1. 將字典轉換為 Strategy 物件
        strategy = Strategy(**strategy_dict)

        # 2. 初始化回測服務
        # 注意：在每次請求中都重新實例化 DBManager 可能效率不高
        # 在正式的應用程式中，應該使用一個共享的、生命週期管理的實例
        db_manager = DBManager(db_path=str(DB_PATH))
        backtester = BacktestingService(db_manager=db_manager)

        # 3. 執行回測
        # BacktestingService.run 是同步的，我們可以用 asyncio.to_thread 來運行它
        # 以避免阻塞 FastAPI 的事件循環
        report: PerformanceReport = await asyncio.to_thread(backtester.run, strategy)

        # 4. 將報告轉換為字典並返回
        return report.model_dump()

    except Exception as e:
        # 在真實應用中，這裡應該有更詳細的錯誤日誌
        print(f"執行回測時發生錯誤: {e}")
        return {"error": str(e)}

# --- 以下是為了方便獨立測試而設的範例 ---
async def main():
    """用於獨立測試 run_backtest 函式的非同步主函式。"""
    print("正在執行獨立的回測測試...")

    # 建立一個模擬的資料庫和一些數據
    # 在真實情境中，資料庫應該由數據工程管線預先建立
    if not DB_PATH.parent.exists():
        DB_PATH.parent.mkdir(parents=True)

    import duckdb
    import pandas as pd
    import numpy as np

    # 模擬因子和價格數據
    dates = pd.to_datetime(pd.date_range(start="2023-01-01", periods=200))
    symbols = ["AAPL", "GOOG"]
    factors_data = []
    for symbol in symbols:
        price = 100 + np.cumsum(np.random.randn(200))
        sma_50 = pd.Series(price).rolling(50).mean()
        rsi_14 = pd.Series(price).rolling(14).apply(lambda x: np.random.rand() * 100) # 簡化 RSI
        for i in range(200):
            factors_data.append({
                "date": dates[i],
                "symbol": symbol,
                "close": price[i],
                "SMA_50": sma_50.iloc[i],
                "RSI_14": rsi_14.iloc[i],
            })

    factors_df = pd.DataFrame(factors_data)

    try:
        con = duckdb.connect(str(DB_PATH))
        con.execute("CREATE OR REPLACE TABLE factors AS SELECT * FROM factors_df")
        con.close()
        print("模擬資料庫和 'factors' 表已成功建立。")
    except Exception as e:
        print(f"建立模擬資料庫失敗: {e}")
        return

    # 定義一個測試策略
    test_strategy = {
        "target_asset": "AAPL",
        "factors": ["SMA_50", "RSI_14"],
        "weights": {"SMA_50": 0.6, "RSI_14": 0.4},
    }

    # 執行回測
    result = await run_backtest(test_strategy)

    # 打印結果
    print("\n回測結果:")
    import json
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
