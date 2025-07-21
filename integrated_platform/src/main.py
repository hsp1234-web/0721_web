# src/main.py

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import os

# 建立 FastAPI 應用實例
app = FastAPI(
    title="整合型應用平台",
    description="由後端 API 驅動的動態前端應用程式",
    version="0.1.0",
)

# 獲取當前檔案的目錄
current_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(current_dir, "static")

# 掛載靜態檔案目錄，讓前端可以被存取
# 注意：在 FastAPI 中，通常我們會將靜態檔案與 API 分開處理，
# 但為了在 Colab 中方便演示，我們將由根路徑提供 index.html
# app.mount("/static", StaticFiles(directory=static_path), name="static")


@app.get("/", response_class=HTMLResponse)
async def read_root():
    """
    提供前端主頁面 (index.html)。
    """
    html_file_path = os.path.join(static_path, "index.html")
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>找不到前端檔案</h1>", status_code=404)


@app.get("/api/apps")
async def get_applications():
    """
    提供可用的應用程式列表。
    這是「元數據驅動 UI」的核心。
    """
    return [
        {
            "id": "transcribe",
            "name": "錄音轉寫服務",
            "icon": "mic",
            "description": "上傳音訊檔案，自動轉換為文字稿。",
        },
        {
            "id": "quant",
            "name": "量化研究框架",
            "icon": "bar-chart-3",
            "description": "執行金融策略回測與數據分析。",
        },
        {
            "id": "placeholder_1",
            "name": "未來功能模組",
            "icon": "box",
            "description": "這是一個尚未啟用的功能佔位符。",
        },
    ]
