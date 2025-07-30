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

import httpx
import json

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get("http://localhost:8080/api/status")
            response.raise_for_status()
            data = response.json()
            if data.get("packages"):
                data["packages"] = json.loads(data["packages"])
            if data.get("apps_status"):
                data["apps_status"] = json.loads(data["apps_status"])
        except (httpx.RequestError, httpx.HTTPStatusError, json.JSONDecodeError) as e:
            data = {"error": str(e)}
    return templates.TemplateResponse("control_panel.html", {"request": request, "data": data})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005)) # 使用一個新的埠號
    uvicorn.run(app, host="0.0.0.0", port=port)
