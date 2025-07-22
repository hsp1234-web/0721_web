"""轉寫服務 API 主應用程式"""
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator
import logging

import aiofiles
import aiosqlite
from fastapi import FastAPI, File, HTTPException, UploadFile, Request
from fastapi.staticfiles import StaticFiles

from prometheus.core.logging.log_manager import LogManager
from prometheus.transcriber.core import DATABASE_FILE, UPLOAD_DIR, initialize_database

# --- 靜態檔案目錄設定 ---
static_dir = Path("static")
static_dir.mkdir(exist_ok=True)

# --- 日誌記錄器設定 ---
log_manager = LogManager(log_file="transcriber_api.log")
logger = log_manager.get_logger(__name__)


# --- 應用程式生命週期管理 ---
import multiprocessing as mp

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """處理應用程式啟動與關閉事件"""
    logger.info("轉寫服務 API 啟動中...")
    await initialize_database()
    # 如果沒有從 CLI 注入佇列，則建立一個新的
    if not hasattr(app.state, 'task_queue'):
        logger.warning("未在 app.state 中找到任務佇列，正在建立新的佇列。")
        app.state.task_queue = mp.Queue()
    yield
    logger.info("轉寫服務 API 已關閉。")
    # 佇列的生命週期由 CLI 管理，此處不關閉


# --- FastAPI 應用程式實例 ---
app = FastAPI(lifespan=lifespan)


# --- API 端點 ---
@app.get("/health", status_code=200, summary="健康檢查")
async def health_check() -> dict[str, str]:
    """提供一個簡單的健康檢查端點，確認服務是否正常運行。"""
    return {"status": "ok"}


@app.post("/upload", status_code=202, summary="上傳音檔並建立轉寫任務")
async def upload_file(
    request: Request,
    file: UploadFile = File(..., description="要上傳的音訊檔案"),
) -> dict[str, str]:
    """
    接收客戶端上傳的音訊檔案，將其儲存至伺服器，並為其建立一個新的轉寫任務。

    - **儲存檔案**: 檔案會以 UUID 重新命名，以避免檔名衝突。
    - **建立任務**: 在資料庫中新增一筆任務記錄。
    - **加入佇列**: 將任務 ID 加入背景處理佇列，交由工人進程處理。
    """
    task_id = str(uuid.uuid4())
    # 確保上傳目錄存在
    UPLOAD_DIR.mkdir(exist_ok=True)
    filepath = UPLOAD_DIR / f"{task_id}_{file.filename}"

    try:
        # 以 1MB 的區塊讀寫檔案，避免一次性載入過大檔案佔用記憶體
        async with aiofiles.open(filepath, "wb") as out_file:
            while content := await file.read(1024 * 1024):
                await out_file.write(content)
        logger.info("檔案 '%s' 已成功上傳至 '%s'", file.filename, filepath)

        # 在資料庫中記錄此任務
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                "INSERT INTO transcription_tasks (id, original_filepath) VALUES (?, ?)",
                (task_id, str(filepath)),
            )
            await db.commit()

        # 將任務 ID 推入佇列
        task_queue = request.app.state.task_queue
        task_queue.put(task_id)
        logger.info("任務 %s 已成功加入轉寫佇列。", task_id)

    except IOError as e:
        logger.exception("檔案操作時發生錯誤: %s", e)
        raise HTTPException(status_code=500, detail="檔案儲存失敗，請檢查伺服器權限或磁碟空間。") from e
    except aiosqlite.Error as e:
        logger.exception("資料庫操作時發生錯誤: %s", e)
        raise HTTPException(status_code=500, detail="無法建立轉寫任務，請檢查資料庫狀態。") from e

    return {"task_id": task_id}


@app.get("/status/{task_id}", summary="查詢轉寫任務狀態")
async def get_task_status(
    task_id: str,
) -> dict[str, Any]:
    """根據任務 ID，查詢並返回該任務的當前狀態、進度及轉寫結果。"""
    try:
        async with aiosqlite.connect(DATABASE_FILE) as db:
            db.row_factory = aiosqlite.Row  # 讓查詢結果可以像字典一樣取值
            async with db.execute(
                "SELECT * FROM transcription_tasks WHERE id = ?", (task_id,)
            ) as cursor:
                task = await cursor.fetchone()

        if task is None:
            raise HTTPException(status_code=404, detail=f"找不到任務 ID: {task_id}")

        return dict(task)

    except aiosqlite.Error as e:
        logger.exception("查詢任務 %s 狀態時發生資料庫錯誤: %s", task_id, e)
        raise HTTPException(status_code=500, detail="查詢任務狀態時發生錯誤。") from e


# --- 掛載靜態檔案 ---
# 將 static 目錄下的檔案作為根路徑 (/) 的靜態資源，並提供 index.html 作為預設頁面
app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")

# --- 直接執行時的備用啟動方式 ---
if __name__ == "__main__":
    import uvicorn
    logger.info("使用 uvicorn 直接啟動 API 伺服器 (僅供開發測試)...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
