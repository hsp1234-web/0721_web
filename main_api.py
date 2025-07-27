# -*- coding: utf-8 -*-
import asyncio
import os
import sqlite3
import uuid
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

import aiofiles
import aiosqlite
import psutil
from fastapi import FastAPI, File, HTTPException, UploadFile

# --- 全域設定與常數 ---
DATABASE_FILE = Path("app_data.db")
UPLOAD_DIR = Path("uploads")
PROMETHEUS_RUN_SCRIPT = "ALL_DATE/0709_wolf_88/run.py"
PROMETHEUS_PROJECT_DIR = "ALL_DATE/0709_wolf_88"

# 最小所需磁碟空間 (MB)
MIN_DISK_SPACE_MB = 100
# 最大可接受記憶體使用率 (%)
MAX_MEMORY_USAGE_PERCENT = 95


# --- 環境檢查模組 ---
class EnvironmentError(Exception):
    """自訂環境錯誤異常"""
    pass

def check_disk_space():
    """檢查剩餘磁碟空間是否充足。"""
    free_space_mb = psutil.disk_usage('/').free / (1024 * 1024)
    if free_space_mb < MIN_DISK_SPACE_MB:
        raise EnvironmentError(f"磁碟空間不足！剩餘 {free_space_mb:.2f} MB。")
    print(f"磁碟空間檢查通過。剩餘 {free_space_mb:.2f} MB。")

def check_memory():
    """檢查記憶體使用率是否在可接受範圍內。"""
    memory_percent = psutil.virtual_memory().percent
    if memory_percent > MAX_MEMORY_USAGE_PERCENT:
        raise EnvironmentError(f"記憶體使用率過高！目前為 {memory_percent}%。")
    print(f"記憶體檢查通過。目前使用率 {memory_percent}%。")


# --- 資料庫模組 ---
async def initialize_database():
    """建立資料庫和所需的資料表。"""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS transcription_tasks (
                id TEXT PRIMARY KEY,
                original_filepath TEXT NOT NULL,
                status TEXT NOT NULL,
                result TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS analysis_tasks (
                id TEXT PRIMARY KEY,
                task_type TEXT NOT NULL,
                status TEXT NOT NULL,
                log_file TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.commit()
    print(f"資料庫 '{DATABASE_FILE}' 已成功初始化。")


# --- FastAPI 生命週期事件 ---
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """處理應用程式啟動與關閉事件。"""
    print("--- 應用程式啟動流程開始 ---")
    # 1. 建立所需目錄
    UPLOAD_DIR.mkdir(exist_ok=True)

    # 2. 執行環境檢查
    try:
        print("步驟 1/2: 執行環境檢查...")
        check_disk_space()
        check_memory()
        print("環境檢查通過。")
    except EnvironmentError as e:
        print(f"致命錯誤：環境檢查失敗，無法啟動應用程式。原因：{e}")
        # 在實際應用中，這裡可以發送警報
        raise RuntimeError(f"環境檢查失敗: {e}") from e

    # 3. 初始化資料庫
    try:
        print("步驟 2/2: 初始化資料庫...")
        await initialize_database()
        print("資料庫初始化完成。")
    except Exception as e:
        print(f"致命錯誤：資料庫初始化失敗。原因：{e}")
        raise RuntimeError(f"資料庫初始化失敗: {e}") from e

    print("--- 應用程式已成功啟動 ---")
    yield
    print("--- 應用程式正在關閉 ---")


# --- FastAPI 應用程式實例 ---
app = FastAPI(lifespan=lifespan)


# --- API 端點 ---

# 核心端點
@app.get("/health", status_code=200)
async def health_check() -> dict[str, str]:
    """健康檢查端點。"""
    return {"status": "ok", "message": "服務運行中"}

# MP3 轉寫服務
@app.post("/upload", status_code=202)
async def upload_file(file: UploadFile = File(...)) -> dict[str, str]:
    """接收檔案上傳，儲存檔案，並建立一個新的轉寫任務。"""
    task_id = str(uuid.uuid4())
    filepath = UPLOAD_DIR / f"{task_id}_{file.filename}"

    try:
        # 儲存檔案
        async with aiofiles.open(filepath, "wb") as out_file:
            while content := await file.read(1024 * 1024):  # 1MB 區塊
                await out_file.write(content)

        # 在資料庫中建立任務紀錄
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                "INSERT INTO transcription_tasks (id, original_filepath, status) VALUES (?, ?, ?)",
                (task_id, str(filepath), "pending"),
            )
            await db.commit()

        # TODO: 將 task_id 推送到真正的背景 worker 佇列
        # 為了演示，這裡直接模擬一個成功的轉寫
        asyncio.create_task(simulate_transcription(task_id, file.filename))

    except Exception as e:
        print(f"上傳失敗: {e}")
        raise HTTPException(status_code=500, detail="檔案操作或資料庫錯誤。")

    return {"task_id": task_id}

async def simulate_transcription(task_id: str, filename: str):
    """模擬一個耗時的轉寫過程並更新資料庫。"""
    await asyncio.sleep(5)  # 模擬 5 秒的處理時間
    transcribed_text = f"這是 '{filename}' 的模擬非同步轉寫結果。"
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute(
            "UPDATE transcription_tasks SET status = ?, result = ? WHERE id = ?",
            ("completed", transcribed_text, task_id)
        )
        await db.commit()
    print(f"任務 {task_id} 已完成轉寫。")


@app.get("/status/{task_id}")
async def get_task_status(task_id: str) -> dict[str, Any]:
    """根據 ID 查詢轉寫任務的狀態和結果。"""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM transcription_tasks WHERE id = ?", (task_id,)) as cursor:
            task = await cursor.fetchone()

    if task is None:
        raise HTTPException(status_code=404, detail="找不到任務 ID")
    return dict(task)


# 金融數據分析服務
@app.post("/analysis/build", status_code=202)
async def start_feature_store_build_endpoint() -> dict[str, Any]:
    """觸發一個 'build-feature-store' 的背景任務。"""
    task_id = str(uuid.uuid4())
    log_file_path = f"/tmp/prometheus_build_{task_id}.log"

    try:
        # 在資料庫中記錄任務
        async with aiosqlite.connect(DATABASE_FILE) as db:
            await db.execute(
                "INSERT INTO analysis_tasks (id, task_type, status, log_file) VALUES (?, ?, ?, ?)",
                (task_id, "build_feature_store", "starting", log_file_path)
            )
            await db.commit()

        # 使用 asyncio.create_subprocess_exec 在背景啟動任務
        # 使用絕對路徑以避免在更改 cwd 後找不到檔案
        python_executable = str(Path(".venv/bin/python").resolve())
        run_script_path = str(Path(PROMETHEUS_RUN_SCRIPT).resolve())
        command = [python_executable, run_script_path, "build-feature-store"]

        # 現在 shebang 行已經硬式編碼，我們只需要執行腳本即可
        process = await asyncio.create_subprocess_exec(
            run_script_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=PROMETHEUS_PROJECT_DIR
        )

        # 建立一個背景任務來處理日誌和監控
        asyncio.create_task(log_and_monitor_process(process, task_id, log_file_path))

        message = (f"已成功啟動 'build-feature-store' 任務。任務 ID: {task_id}。"
                   f"日誌請查看: {log_file_path}")
        return {"status": "success", "message": message, "task_id": task_id}

    except Exception as e:
        error_msg = f"啟動分析任務時發生錯誤: {e}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=f"伺服器內部錯誤: {e}")

async def log_and_monitor_process(process: asyncio.subprocess.Process, task_id: str, log_file_path: str):
    """即時讀取子進程的輸出寫入日誌檔案，並在完成後更新資料庫。"""
    async with aiofiles.open(log_file_path, "w") as log_file:
        while True:
            # 同時讀取 stdout 和 stderr
            line = await process.stdout.readline()
            err_line = await process.stderr.readline()

            if line:
                await log_file.write(line.decode())
            if err_line:
                await log_file.write(err_line.decode())

            if not line and not err_line and process.returncode is not None:
                break
            await asyncio.sleep(0.1)

    status = "completed" if process.returncode == 0 else "failed"
    async with aiosqlite.connect(DATABASE_FILE) as db:
        await db.execute(
            "UPDATE analysis_tasks SET status = ? WHERE id = ?",
            (status, task_id)
        )
        await db.commit()
    print(f"分析任務 {task_id} 已執行完畢，狀態: {status} (返回碼: {process.returncode})。")


@app.get("/analysis/status/{task_id}")
async def get_analysis_task_status(task_id: str) -> dict[str, Any]:
    """根據 ID 查詢分析任務的狀態。"""
    async with aiosqlite.connect(DATABASE_FILE) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM analysis_tasks WHERE id = ?", (task_id,)) as cursor:
            task = await cursor.fetchone()

    if task is None:
        raise HTTPException(status_code=404, detail="找不到任務 ID")
    return dict(task)

# --- Uvicorn 啟動 (如果直接執行此檔案) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
