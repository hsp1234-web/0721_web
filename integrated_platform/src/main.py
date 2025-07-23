# integrated_platform/src/main.py
import logging
import os
import asyncio
import time
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# --- 導入集中化配置與業務邏輯 ---
from . import config
from . import integrated_logic

# --- 設定結構化日誌 ---
# 移除 basicConfig，改為在啟動時動態設定 handler
logger = logging.getLogger()
logger.setLevel(logging.INFO) # 設定根 logger 的級別

# --- 全域變數與模擬資料庫 ---
# 使用簡單的字典來模擬資料庫和任務儲存
mock_tasks = {}
# 全局實例化模擬任務佇列
mock_task_queue = integrated_logic.MockTaskQueue()

# --- 應用程式生命週期事件 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式啟動與關閉時的生命週期事件。
    """
    # --- 日誌系統與 Colab 環境整合 ---
    # 檢查環境變數，如果設定了 LOG_DB_PATH，就使用 SQLiteHandler
    # 這使得應用程式可以將日誌無縫寫入 Colab UI 的資料庫
    log_db_path_str = os.getenv("LOG_DB_PATH")
    if log_db_path_str:
        from .sqlite_log_handler import SQLiteHandler
        log_db_path = Path(log_db_path_str)
        # 確保目錄存在
        log_db_path.parent.mkdir(exist_ok=True)
        sqlite_handler = SQLiteHandler(db_path=log_db_path)

        # 為 handler 設定一個 formatter，使其只輸出訊息本身
        formatter = logging.Formatter('%(message)s')
        sqlite_handler.setFormatter(formatter)

        logger.addHandler(sqlite_handler)
        logger.info("偵測到 LOG_DB_PATH，已啟用 SQLite 日誌處理器。")
    else:
        # 如果沒有設定環境變數，則退回到標準的控制台輸出
        stream_handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        logger.info("未偵測到 LOG_DB_PATH，日誌將輸出至控制台。")

    logger.info("應用程式啟動中，開始執行啟動程序...")

    # 確保上傳目錄存在
    Path(config.UPLOAD_DIR).mkdir(exist_ok=True)
    logger.info(f"確保上傳目錄 '{config.UPLOAD_DIR}' 存在。")

    # 啟動模擬轉寫工人作為背景任務
    worker = integrated_logic.MockTranscriberWorker(mock_tasks, mock_task_queue)
    asyncio.create_task(worker.process_tasks())
    logger.info("模擬轉寫工人已作為背景任務啟動。")

    logger.info("應用程式啟動程序完成。")
    yield
    logger.info("伺服器應用已關閉。")

# --- FastAPI 應用程式實例 ---
app = FastAPI(title="整合型應用平台 (模擬版)", lifespan=lifespan)

# --- 中介軟體: 記錄所有傳入請求 ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"收到請求: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# --- 核心與靜態檔案路由 ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    static_path = Path(__file__).resolve().parent / "static"
    html_file_path = static_path / "index.html"
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        logger.error("找不到前端檔案 (index.html)。")
        return HTMLResponse(content="<h1>錯誤：找不到前端檔案 (index.html)</h1>", status_code=404)

@app.get("/api/apps")
async def get_applications():
    apps_list = [
        {"id": "transcribe", "name": "錄音轉寫服務 (模擬)", "icon": "mic", "description": "上傳音訊檔案，模擬非同步轉寫。"},
        {"id": "quant", "name": "量化研究框架 (模擬)", "icon": "bar-chart-3", "description": "觸發模擬的金融策略回測與分析。"},
    ]
    return apps_list

@app.get(config.HEALTH_CHECK_ENDPOINT)
async def health_check():
    # 在模擬版中，我們簡化健康檢查，總是返回成功
    return {"status": "ok", "message": "服務運行正常 (模擬模式)"}

# --- 鳳凰專案：MP3 錄音轉寫服務 API (模擬版) ---
@app.post("/upload")
async def upload_audio(file: UploadFile = File(...)):
    task_id = str(uuid.uuid4())
    # 增加一個 'error' 關鍵字來觸發模擬失敗
    filename = f"{task_id}_{'error' if 'error' in file.filename else file.filename}"
    file_location = os.path.join(config.UPLOAD_DIR, filename)

    try:
        with open(file_location, "wb") as f:
            f.write(await file.read())
        logger.info(f"檔案 '{file.filename}' 已儲存為 '{file_location}'。")

        task = integrated_logic.TranscriptionTask(task_id=task_id, file_path=file_location)
        mock_tasks[task_id] = task
        mock_task_queue.put(task_id)

        logger.info(f"轉寫任務 {task_id} 已創建並加入佇列。")
        return {"task_id": task_id, "message": "檔案已上傳，轉寫任務已啟動。"}
    except Exception as e:
        logger.error(f"檔案上傳或任務創建失敗: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"檔案上傳或任務創建失敗: {str(e)}")

@app.get("/status/{task_id}")
async def get_transcription_status(task_id: str):
    task = mock_tasks.get(task_id)
    if not task:
        logger.warning(f"查詢失敗，任務 ID 不存在: {task_id}")
        raise HTTPException(status_code=404, detail="任務 ID 不存在。")
    logger.info(f"查詢任務 {task_id} 狀態: {task.status}")
    return task

# --- 普羅米修斯之火：金融因子工程與模擬框架 API (模擬版) ---
class FactorCalculationRequest(BaseModel):
    asset_symbol: str

@app.post("/financial/factors/calculate")
async def calculate_factors(request: FactorCalculationRequest, background_tasks: BackgroundTasks):
    pipeline = integrated_logic.MockDataPipeline(factors_db_path=config.FACTORS_DB_PATH)
    background_tasks.add_task(pipeline.run_factor_calculation, request.asset_symbol)
    logger.info(f"觸發 {request.asset_symbol} 的模擬金融因子計算背景任務。")
    return {"message": f"模擬金融因子計算任務已啟動，執行日誌請見伺服器控制台。"}

class BacktestRequest(BaseModel):
    strategy_config: dict

@app.post("/financial/backtest")
async def run_backtest(request: BacktestRequest, background_tasks: BackgroundTasks):
    service = integrated_logic.MockBacktestingService(factors_db_path=config.FACTORS_DB_PATH)
    background_tasks.add_task(service.run_backtest, request.strategy_config)
    logger.info(f"觸發模擬策略回測背景任務，策略配置: {request.strategy_config}")
    return {"message": "模擬策略回測任務已啟動，執行日誌請見伺服器控制台。"}

class EvolutionRequest(BaseModel):
    generations: int

@app.post("/financial/evolve")
async def evolve_strategy(request: EvolutionRequest, background_tasks: BackgroundTasks):
    chamber = integrated_logic.MockEvolutionChamber(factors_db_path=config.FACTORS_DB_PATH)
    background_tasks.add_task(chamber.evolve_strategy, request.generations)
    logger.info(f"觸發模擬策略演化背景任務，世代數: {request.generations}")
    return {"message": "模擬策略演化任務已啟動，執行日誌請見伺服器控制台。"}

@app.get("/financial/factors/list")
async def list_factors():
    logger.info("列出模擬金融因子。")
    return {"factors": ["mock_PE_ratio", "mock_PB_ratio", "mock_VIX_correlation"]}

# --- 應用程式啟動 ---
if __name__ == "__main__":
    import uvicorn
    logger.info(f"啟動 Uvicorn 伺服器，監聽埠號: {config.UVICORN_PORT}")
    uvicorn.run(
        "integrated_platform.src.main:app",
        host="0.0.0.0",
        port=config.UVICORN_PORT,
        reload=True
    )
