import asyncio
import random  # nosec B404
import uuid
from typing import Any, Dict

MOCK_TASK_DB: Dict[str, Dict[str, Any]] = {}


async def start_backtest_task() -> str:
    """創建一個回測任務並返回其 ID。"""
    task_id = str(uuid.uuid4())
    MOCK_TASK_DB[task_id] = {
        "id": task_id,
        "status": "pending",
        "progress": 0,
        "result": None,
    }
    return task_id


async def get_backtest_status(task_id: str) -> Dict[str, Any] | None:
    """獲取回測任務的狀態。"""
    return MOCK_TASK_DB.get(task_id)


async def run_mock_backtest(task_id: str) -> None:
    """一個模擬的背景回測任務。"""
    task = MOCK_TASK_DB[task_id]
    task["status"] = "running"
    for i in range(1, 101):
        await asyncio.sleep(random.uniform(0.1, 0.3))  # nosec B311
        task["progress"] = i
    task["status"] = "completed"
    task["result"] = {"pnl": random.uniform(-1000, 5000), "sharpe_ratio": 2.1}  # nosec B311
