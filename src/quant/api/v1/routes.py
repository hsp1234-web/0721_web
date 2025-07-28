# -*- coding: utf-8 -*-
"""
量化 App - API V1 路由
"""
import sys
from pathlib import Path

from fastapi import APIRouter, Body, HTTPException
from pydantic import BaseModel, Field

# --- 設置導入路徑 ---
# 確保可以從 quant 目錄導入 logic 模組
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.quant.logic import analysis, database

# 建立一個 APIRouter 實例，我們可以稍後將它包含到主 App 中
router = APIRouter(
    prefix="/v1",  # 所有這個 router 的路由都會有 /v1 的前綴
    tags=["Quantitative Analysis V1"],  # 在 OpenAPI 文檔中為這組路由分組
)

# --- Pydantic 模型定義 ---
# 使用 Pydantic 來定義請求主體的結構和驗證規則
class BacktestRequest(BaseModel):
    stock_id: str = Field(...,
                           description="要進行回測的股票代號",
                           json_schema_extra={"example": "2330.TW"})
    start_date: str = Field(...,
                             description="回測開始日期",
                             json_schema_extra={"example": "2023-01-01"})
    end_date: str = Field(...,
                           description="回測結束日期",
                           json_schema_extra={"example": "2024-01-01"})

# --- API 路由定義 ---

@router.post("/backtest", summary="執行一個簡單的回測策略")
async def perform_backtest(request: BacktestRequest = Body(...)):
    """
    接收回測請求，執行簡單的移動平均線交叉策略，並返回結果。
    結果也會被儲存到資料庫中。
    """
    # 呼叫業務邏輯層的函式
    result = analysis.run_simple_backtest(
        stock_id=request.stock_id,
        start_date=request.start_date,
        end_date=request.end_date,
    )

    # 明確地檢查業務邏輯層是否返回了錯誤
    if "error" in result:
        # 如果有錯誤，就引發一個 400 Bad Request 異常，並將錯誤訊息作為詳細內容
        raise HTTPException(status_code=400, detail=result["error"])

    # 如果沒有錯誤，則將成功的結果存入資料庫
    try:
        database.db_manager.save_backtest_result(result)
    except Exception as e:
        # 如果資料庫儲存失敗，這是一個伺服器內部問題
        raise HTTPException(status_code=500, detail=f"回測成功，但結果存儲失敗: {e}")

    return result

@router.get("/backtest/results", summary="獲取所有歷史回測結果")
async def get_backtest_results():
    """
    從資料庫中讀取所有已儲存的回測結果紀錄。
    """
    try:
        results_df = database.db_manager.get_all_backtest_results()
        # 將 DataFrame 轉換為 JSON 格式的回應
        return results_df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"讀取回測結果時發生內部錯誤: {e}")
