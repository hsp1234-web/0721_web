from fastapi import APIRouter, HTTPException
from typing import Dict

# 假設的插件邏輯
from .src.logic import run_quant_analysis_logic

router = APIRouter()

@router.post("/run-analysis", status_code=202)
async def run_analysis(params: Dict) -> Dict[str, str]:
    """
    接收分析參數，並啟動一個模擬的量化分析任務。
    """
    try:
        task_id = await run_quant_analysis_logic(params)
        return {"task_id": task_id, "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
def health_check():
    return {"status": "ok", "plugin": "quant"}
