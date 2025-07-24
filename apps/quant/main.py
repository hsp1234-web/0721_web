# -*- coding: utf-8 -*-
from fastapi import APIRouter, BackgroundTasks

# 導入此 App 的業務邏輯
from . import logic

# --- App 資訊 ---
app_info = {
    "id": "quant",
    "name": "量化研究框架 (模擬)",
    "icon": "bar-chart-3",
    "description": "觸發模擬的金融策略回測與分析。",
    "version": "1.0"
}

# --- API 路由器 ---
router = APIRouter(
    prefix="/api/quant",
    tags=["Quant App"],
)

@router.post("/backtest")
async def run_backtest(background_tasks: BackgroundTasks):
    """
    觸發一個模擬的背景回測任務。
    """
    task_id = await logic.start_backtest_task()
    background_tasks.add_task(logic.run_mock_backtest, task_id)
    return {"message": "模擬策略回測任務已啟動。", "task_id": task_id}

@router.get("/status/{task_id}")
async def get_backtest_status(task_id: str):
    """
    查詢回測任務的狀態。
    """
    return await logic.get_backtest_status(task_id)
