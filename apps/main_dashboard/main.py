# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os

app = FastAPI()

from pathlib import Path

# --- 設置模板目錄 ---
# 使用絕對路徑，以避免在不同執行環境下出現問題
# Path(__file__) -> /app/apps/main_dashboard/main.py
# .parent -> /app/apps/main_dashboard
# / "templates" -> /app/apps/main_dashboard/templates
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    fake_data = {
        "status": "ok",
        "current_stage": "completed",
        "apps_status": {
            "quant": "running",
            "transcriber": "running",
            "main_dashboard": "running"
        },
        "action_url": "http://localhost:8005/",
        "cpu_usage": 12.3,
        "ram_usage": 45.6,
        "logs": [
            {"timestamp": "2024-01-01 12:00:00", "level": "INFO", "message": "系統啟動"},
            {"timestamp": "2024-01-01 12:00:01", "level": "INFO", "message": "Quant 服務已啟動"},
            {"timestamp": "2024-01-01 12:00:02", "level": "INFO", "message": "Transcriber 服務已啟動"},
            {"timestamp": "2024-01-01 12:00:03", "level": "INFO", "message": "Main Dashboard 已啟動"},
        ]
    }
    return templates.TemplateResponse("control_panel.html", {"request": request, "data": fake_data})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005)) # 使用一個新的埠號
    uvicorn.run(app, host="0.0.0.0", port=port)
