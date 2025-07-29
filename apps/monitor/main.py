# -*- coding: utf-8 -*-
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os
from core_utils.shared_log_queue import get_log

app = FastAPI()

templates = Jinja2Templates(directory="apps/monitor/templates")

@app.get("/api/long-poll-logs")
async def long_poll_logs():
    """
    使用長輪詢來獲取日誌。
    後端會掛起請求，直到有新日誌或超時。
    """
    try:
        # 使用 asyncio.to_thread 在非同步環境中執行阻塞的 get_log()
        message = await asyncio.to_thread(get_log)
        if message:
            return JSONResponse(content={"status": "new_message", "message": message})
        else:
            # 如果 get_log() 超時並返回 None，則發送一個心跳訊息
            return JSONResponse(content={"status": "no_message"})
    except Exception as e:
        return JSONResponse(content={"status": "error", "message": str(e)}, status_code=500)


@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    提供監控儀表板的主頁面。
    """
    return templates.TemplateResponse("dashboard.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)
