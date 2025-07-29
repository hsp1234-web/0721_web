# -*- coding: utf-8 -*-
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from core_utils.shared_log_queue import get_log, log_queue

app = FastAPI()

# 設置模板目錄
templates = Jinja2Templates(directory="apps/monitor/templates")

async def log_generator():
    """一個非同步生成器，用於從佇列中獲取日誌並格式化為 SSE 格式"""
    while True:
        try:
            # 使用 asyncio.to_thread 來非阻塞地獲取日誌
            message = await asyncio.to_thread(log_queue.get)
            # SSE 格式: "data: message\n\n"
            yield f"data: {message}\n\n"
            # 給事件循環一點喘息的機會
            await asyncio.sleep(0.01)
        except Exception:
            # 如果發生任何錯誤，也將其發送到前端
            yield f"data: [MONITOR_ERROR] 日誌串流發生錯誤。\n\n"
            await asyncio.sleep(1)


@app.get("/api/logs")
async def stream_logs():
    """
    使用 Server-Sent Events (SSE) 將後端日誌即時串流到前端。
    """
    return StreamingResponse(log_generator(), media_type="text/event-stream")


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    提供監控儀表板的主頁面。
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    # 這個部分允許我們獨立運行 monitor app 進行測試
    port = int(os.environ.get("PORT", 8003))
    print(f"獨立運行 Monitor App 於 http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
