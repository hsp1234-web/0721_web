import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse

# --- 導入集中化配置 ---
from . import config

# --- 設定結構化日誌 ---
# 移除舊的 LogManager，改用 Python 標準 logging 模組
# 這使得日誌輸出到控制台，在 Colab 和 Docker 環境中更易於監控
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# --- 全域變數與應用程式狀態 ---
# 確保上傳目錄存在
Path(config.UPLOAD_DIR).mkdir(exist_ok=True)

# 模擬的應用程式狀態，用於健康檢查
whisper_model_loaded = False
db_connections_ok = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    應用程式啟動與關閉時的生命週期事件。
    """
    global whisper_model_loaded, db_connections_ok
    logger.info("應用程式啟動中，開始執行啟動程序...")

    try:
        # 步驟 1: 檢查資料庫連線 (此為示意，未來將替換為真實的檢查)
        # 這裡我們暫時假設連線總是成功的
        # import sqlite3
        # import duckdb
        # conn_transcription = sqlite3.connect(config.LOG_DB_PATH)
        # conn_transcription.close()
        # conn_factors = duckdb.connect(config.FACTORS_DB_PATH)
        # conn_factors.close()
        db_connections_ok = True
        logger.info(f"資料庫連線檢查完成。狀態: {'成功' if db_connections_ok else '失敗'}")

        # 步驟 2: 載入 AI 模型 (此為示意，未來將非同步載入真實模型)
        # 我們將模型載入狀態記錄下來，以供健康檢查使用
        # from faster_whisper import WhisperModel
        # global model
        # model = WhisperModel(config.WHISPER_MODEL_NAME, device="cuda", compute_type="float16")
        whisper_model_loaded = True # 在此版本中，我們假設模型總是能載入
        logger.info(f"Whisper 模型 '{config.WHISPER_MODEL_NAME}' 載入狀態: {'成功' if whisper_model_loaded else '失敗'}")

        logger.info("應用程式啟動程序完成。")
        yield

    except Exception as e:
        logger.error(f"應用程式啟動時發生嚴重錯誤: {e}", exc_info=True)
        # 如果啟動失敗，將狀態設為不健康
        db_connections_ok = False
        whisper_model_loaded = False
    finally:
        logger.info("伺服器應用已關閉。")


app = FastAPI(title="整合型應用平台", lifespan=lifespan)

# --- 中介軟體: 記錄所有傳入請求 ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"收到請求: {request.method} {request.url.path}")
    response = await call_next(request)
    return response

# --- 核心路由 ---
@app.get("/", response_class=HTMLResponse)
async def read_root():
    static_path = Path(__file__).resolve().parent / "static"
    html_file_path = static_path / "index.html"
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            logger.info("成功提供前端靜態檔案 (index.html)。")
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        logger.error("找不到前端檔案 (index.html)。")
        return HTMLResponse(content="<h1>錯誤：找不到前端檔案 (index.html)</h1>", status_code=404)

@app.get("/api/apps")
async def get_applications():
    logger.debug("正在查詢可用的應用程式列表。")
    apps_list = [
        {"id": "transcribe", "name": "錄音轉寫服務", "icon": "mic", "description": "上傳音訊檔案，自動轉換為文字稿。"},
        {"id": "quant", "name": "量化研究框架", "icon": "bar-chart-3", "description": "執行金融策略回測與數據分析。"},
    ]
    logger.info(f"成功返回 {len(apps_list)} 個應用程式。")
    return apps_list

@app.get(config.HEALTH_CHECK_ENDPOINT)
async def health_check():
    """
    精確的健康檢查端點，驗證應用程式核心組件的就緒狀態。
    """
    logger.debug("執行健康檢查...")
    status_summary = {
        "status": "ok",
        "message": "服務運行正常",
        "details": {
            "database_connections": "ok" if db_connections_ok else "failed",
            "whisper_model_loaded": "ok" if whisper_model_loaded else "failed"
        }
    }

    if not db_connections_ok or not whisper_model_loaded:
        status_summary["status"] = "unhealthy"
        messages = []
        if not db_connections_ok:
            messages.append("資料庫連線失敗")
        if not whisper_model_loaded:
            messages.append("Whisper 模型未載入")
        status_summary["message"] = "; ".join(messages)
        logger.warning(f"健康檢查失敗: {status_summary['message']}")
        raise HTTPException(status_code=503, detail=status_summary)

    logger.info("健康檢查通過。")
    return status_summary


# --- 應用程式啟動 ---
if __name__ == "__main__":
    import uvicorn
    logger.info(f"啟動 Uvicorn 伺服器，監聽埠號: {config.UVICORN_PORT}")
    # 使用 uvicorn 來啟動應用程式
    # host="0.0.0.0" 讓服務可以從外部網路存取
    # reload=True 會在程式碼變更時自動重啟伺服器，方便開發
    uvicorn.run(
        "integrated_platform.src.main:app",
        host="0.0.0.0",
        port=config.UVICORN_PORT,
        reload=True
    )
