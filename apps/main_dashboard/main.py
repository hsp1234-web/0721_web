# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import uvicorn
import os

app = FastAPI()

# 使用相對於目前檔案位置的絕對路徑，確保無論從哪裡執行，路徑都正確
BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("control_panel.html", {"request": request})

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """一個簡單的健康檢查端點，用於確認服務是否正在運行。"""
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005)) # 使用一個新的埠號
    uvicorn.run(app, host="0.0.0.0", port=port)
