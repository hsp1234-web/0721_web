# -*- coding: utf-8 -*-
import asyncio
import random
import uuid
from typing import Dict, Any

# --- 模擬資料庫 ---
MOCK_TASK_DB: Dict[str, Dict[str, Any]] = {}

async def start_backtest_task() -> str:
    """
    創建一個回測任務並返回其 ID。
    """
    task_id = str(uuid.uuid4())
    MOCK_TASK_DB[task_id] = {
        "status": "queued",
        "progress": 0,
        "result": None,
    }
    return task_id

async def get_backtest_status(task_id: str) -> Dict[str, Any] | None:
    """
    獲取回測任務的狀態。
    """
    return MOCK_TASK_DB.get(task_id)

async def run_mock_backtest(task_id: str):
    """
    一個模擬的背景回測任務。
    """
    task = MOCK_TASK_DB[task_id]
    task["status"] = "running"

    for i in range(1, 101):
        await asyncio.sleep(random.uniform(0.1, 0.3))
        task["progress"] = i

    task["status"] = "completed"
    task["result"] = {
        "sharpe_ratio": 1.85,
        "max_drawdown": -0.15,
        "total_return": 0.34
    }
    print(f"背景回測任務 {task_id} 完成。")
