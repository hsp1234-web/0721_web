# 繁體中文: main.py - 統一指揮中心

import multiprocessing as mp
import threading
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Depends

# 導入重構後的業務模組和設定
from apps.transcriber.core import get_config, initialize_database, BaseConfig
from apps.transcriber.transcriber_worker import worker_main_loop
from apps.quant import logic as quant_logic
from apps.transcriber import logic as transcriber_logic

# --- 設定 ---
# 在真實應用中，這裡可以透過環境變數或其他方式來決定要載入哪個設定
CONFIG = get_config("testing")

# --- 背景工作者管理 ---
worker_process = None

def start_transcriber_worker(config: BaseConfig):
    """在一個獨立的行程中啟動轉錄工人"""
    global worker_process
    worker_process = mp.Process(
        target=worker_main_loop,
        args=(config,),
        name="TranscriberWorker"
    )
    worker_process.start()
    print(f"轉錄工人行程已啟動 (PID: {worker_process.pid})")

def stop_transcriber_worker():
    """停止轉錄工人行程"""
    global worker_process
    if worker_process and worker_process.is_alive():
        print("正在停止轉錄工人行程...")
        worker_process.terminate()
        worker_process.join(timeout=5)
        print("轉錄工人行程已停止。")

# --- FastAPI 生命週期管理 ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """處理應用程式啟動與關閉事件"""
    print("--- 指揮中心啟動程序開始 ---")

    # 1. 初始化轉錄服務所需的資料庫
    await initialize_database(CONFIG)
    print("轉錄服務資料庫已初始化。")

    # 2. 在背景啟動轉錄工人
    start_transcriber_worker(CONFIG)

    yield

    print("--- 指揮中心關閉程序開始 ---")
    # 停止背景工人
    stop_transcriber_worker()
    print("指揮中心已成功關閉。")

# --- FastAPI 應用實例 ---
app = FastAPI(
    title="統一指揮中心",
    description="整合量化分析與語音轉錄服務的 API",
    version="1.0.0",
    lifespan=lifespan,
)

# --- 依賴注入 ---
def get_config_dependency() -> BaseConfig:
    """提供設定物件作為 FastAPI 的依賴項"""
    return CONFIG

# --- API 路由器 ---
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Any, Dict

# 建立一個給 Quant 服務的路由器
quant_router = APIRouter(prefix="/api/quant", tags=["量化分析引擎"])

@quant_router.post("/backtest", response_model=Dict[str, Any])
async def run_backtest_endpoint(strategy_dict: Dict[str, Any]):
    """
    接收策略定義並執行回測。
    """
    # 注意：這裡的調用是非同步的，因為我們在 logic.py 中使用了 asyncio.to_thread
    result = await quant_logic.run_backtest(strategy_dict)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])
    return result

# 建立一個給 Transcriber 服務的路由器
transcriber_router = APIRouter(prefix="/api/transcriber", tags=["非同步轉錄服務"])

@transcriber_router.post("/upload", response_model=Dict[str, str])
async def upload_audio_file(
    file: UploadFile = File(...),
    config: BaseConfig = Depends(get_config_dependency)
):
    """
    上傳音檔並創建一個新的轉錄任務。
    """
    return await transcriber_logic.submit_transcription_task(file, config)

@transcriber_router.get("/status/{task_id}", response_model=Dict[str, Any])
async def get_transcription_status(
    task_id: str,
    config: BaseConfig = Depends(get_config_dependency)
):
    """
    查詢轉錄任務的狀態與結果。
    """
    status = await transcriber_logic.get_task_status(task_id, config)
    if status is None:
        raise HTTPException(status_code=404, detail="找不到該任務 ID")
    return status

# 將路由器掛載到主應用上
app.include_router(quant_router)
app.include_router(transcriber_router)

if __name__ == "__main__":
    import uvicorn
    # 這裡的 reload=True 在開發時很有用，但在生產中應設為 False
    uvicorn.run(app, host="127.0.0.1", port=8000)
