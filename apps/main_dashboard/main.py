# -*- coding: utf-8 -*-
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import uvicorn
import os
from pathlib import Path

app = FastAPI()

# 設置模板和靜態檔案目錄
templates = Jinja2Templates(directory="apps/main_dashboard/templates")
app.mount("/static", StaticFiles(directory="apps/main_dashboard/static"), name="static")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """
    提供主操作儀表板頁面。
    """
    return templates.TemplateResponse("control_panel.html", {"request": request})

@app.get("/api/get-full-log", response_class=PlainTextResponse)
async def get_full_log():
    """
    一次性讀取並返回 launch_logs.txt 的全部內容。
    """
    log_file_path = Path("launch_logs.txt")
    if not log_file_path.exists():
        raise HTTPException(status_code=404, detail="日誌檔案尚未產生。")

    return log_file_path.read_text(encoding='utf-8')


if __name__ == "__main__":
    # 這個部分允許我們獨立運行 dashboard app 進行測試
    port = int(os.environ.get("PORT", 8004)) # 使用一個新的埠號
    uvicorn.run(app, host="0.0.0.0", port=port)
