# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import uvicorn
import os

app = FastAPI()

templates = Jinja2Templates(directory="apps/main_dashboard/templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("control_panel.html", {"request": request})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8005)) # 使用一個新的埠號
    uvicorn.run(app, host="0.0.0.0", port=port)
