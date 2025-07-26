from typing import Any, Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException

from . import logic

router = APIRouter()


@router.post("/backtest")
async def run_backtest(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """觸發一個模擬的背景回測任務。"""
    task_id = await logic.start_backtest_task()
    background_tasks.add_task(logic.run_mock_backtest, task_id)
    return {"message": "Backtest task started.", "task_id": task_id}


@router.get("/status/{task_id}")
async def get_backtest_status(task_id: str) -> Dict[str, Any]:
    """查詢回測任務的狀態。"""
    status = await logic.get_backtest_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Task not found")
    return status


@router.get("/data")
async def get_quant_data() -> Dict[str, Any]:
    """提供一些模擬的量化數據。"""
    return {
        "symbol": "BTC/USDT",
        "timestamp": "2025-07-26T10:00:00Z",
        "price": 100000.0,
        "volume": 123.456,
    }
