# -*- coding: utf-8 -*-
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from core_utils.shared_log_queue import get_log, log_queue

app = FastAPI()

templates = Jinja2Templates(directory="apps/monitor/templates")

async def log_generator():
    while True:
        try:
            message = await asyncio.to_thread(log_queue.get)
            yield f"data: {message}\n\n"
            await asyncio.sleep(0.01)
        except Exception:
            yield f"data: [MONITOR_ERROR] 日誌串流發生錯誤。\n\n"
            await asyncio.sleep(1)

@app.get("/api/logs")
async def stream_logs():
    return StreamingResponse(log_generator(), media_type="text/event-stream")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8003))
    print(f"獨立運行 Monitor App 於 http://localhost:{port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
