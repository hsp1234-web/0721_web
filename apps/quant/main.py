# apps/quant/main.py
from fastapi import APIRouter, HTTPException
from .logic import run_backtest, BacktestRequest

# 建立一個新的 API 路由器，並為其所有路由設定統一的前綴
# FastAPI 主應用會自動偵測並包含這個路由器
router = APIRouter(prefix="/api/quant", tags=["量化分析"])

@router.post("/backtest")
async def backtest_endpoint(request: BacktestRequest):
    """
    執行策略回測的 API 端點。

    接收一個包含策略參數的 JSON 物件，返回回測的績效結果。
    """
    try:
        # 調用核心業務邏輯
        result = run_backtest(request)
        return result
    except Exception as e:
        # 處理潛在的錯誤
        raise HTTPException(status_code=500, detail=f"執行回測時發生錯誤: {e}")
