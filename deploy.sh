#!/bin/bash

# 【磐石協議 v1.0：Colab 一鍵部署腳本】
# 本腳本將自動化所有設定，實現對專案的「零接觸」極速部署。
# 任何指令失敗都會立即中止腳本。
set -e

# --- [階段 1] 環境設定 ---
echo "✅ [1/5] 正在設定環境..."
pip install poetry > /dev/null 2>&1
export PATH="/root/.local/bin:$PATH"
echo "Poetry 已安裝並設定。"

# --- [階段 2] 建立專案結構與檔案 ---
PROJECT_DIR="integrated_platform"
echo "✅ [2/5] 正在建立專案於 '$PROJECT_DIR'..."
mkdir -p "$PROJECT_DIR/src/static"

# 使用 cat 與 EOF 寫入 pyproject.toml
cat > "$PROJECT_DIR/pyproject.toml" << 'EOF'
[tool.poetry]
name = "integrated-platform"
version = "0.1.0"
description = "API-driven dynamic frontend application"
authors = ["Commander"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.9"
fastapi = "*"
uvicorn = {extras = ["standard"], version = "*"}

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
EOF

# 寫入 src/main.py (後端程式碼)
cat > "$PROJECT_DIR/src/main.py" << 'EOF'
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import os

app = FastAPI(
    title="整合型應用平台",
    description="由後端 API 驅動的動態前端應用程式",
    version="0.1.0",
)

# 獲取當前檔案的目錄來定位靜態檔案
current_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(current_dir, "static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    """提供前端主頁面 (index.html)。"""
    html_file_path = os.path.join(static_path, "index.html")
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>錯誤：找不到前端檔案 (index.html)</h1>", status_code=404)

@app.get("/api/apps")
async def get_applications():
    """提供可用的應用程式列表。這是「元數據驅動 UI」的核心。"""
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
EOF

# 寫入 src/static/index.html (前端程式碼)
cat > "$PROJECT_DIR/src/static/index.html" << 'EOF'
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>整合型應用平台</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        @import url('https://rsms.me/inter/inter.css');
        html { font-family: 'Inter', sans-serif; }
        body { background-color: #f1f5f9; }
    </style>
</head>
<body class="antialiased text-slate-800">
    <div id="main-container" class="container mx-auto p-4 md:p-8 max-w-5xl">
        <header class="mb-8">
            <h1 id="page-title" class="text-3xl md:text-4xl font-bold text-slate-900">應用程式儀表板</h1>
            <p id="page-subtitle" class="text-slate-600 mt-1">請選擇一項服務以繼續</p>
        </header>
        <main id="content-area" class="transition-opacity duration-300"></main>
    </div>
    <script>
        const contentArea = document.getElementById('content-area');
        const pageTitle = document.getElementById('page-title');
        const pageSubtitle = document.getElementById('page-subtitle');
        const createCard = (app) => `<div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer" onclick="showAppPlaceholder('${app.name}', '${app.description}')"><div class="p-6"><div class="flex items-center space-x-4"><div class="flex-shrink-0"><div class="w-12 h-12 bg-indigo-500 text-white rounded-lg flex items-center justify-center"><i data-lucide="${app.icon}"></i></div></div><div><div class="text-xl font-medium text-black">${app.name}</div><p class="text-slate-500">${app.description}</p></div></div></div></div>`;
        const createPlaceholder = (appName, appDescription) => `<div class="bg-white p-8 rounded-xl shadow-md"><button onclick="renderDashboard()" class="flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-semibold mb-6"><i data-lucide="arrow-left" class="w-4 h-4 mr-2"></i>返回儀表板</button><h2 class="text-2xl font-bold mb-2">${appName}</h2><p class="text-slate-600 mb-6">${appDescription}</p><div class="border-t border-slate-200 pt-6"><h3 class="font-semibold mb-4">功能佔位符</h3><div class="bg-slate-50 p-6 rounded-lg text-center text-slate-500"><p>此處將會是「${appName}」的實際操作介面。</p><p class="mt-2">後續的業務邏輯將會在這裡實現。</p></div></div></div>`;
        const renderDashboard = async () => {
            pageTitle.textContent = '應用程式儀表板';
            pageSubtitle.textContent = '請選擇一項服務以繼續';
            contentArea.innerHTML = '<p class="text-slate-500">正在從後端載入功能列表...</p>';
            try {
                const response = await fetch('/api/apps');
                if (!response.ok) throw new Error(`無法取得應用程式列表 (HTTP ${response.status})`);
                const apps = await response.json();
                const cardsHTML = apps.map(createCard).join('');
                contentArea.innerHTML = `<div class="grid grid-cols-1 md:grid-cols-2 gap-6">${cardsHTML}</div>`;
            } catch (error) {
                contentArea.innerHTML = `<p class="text-red-600 font-semibold">錯誤: ${error.message}</p>`;
            } finally {
                lucide.createIcons();
            }
        };
        const showAppPlaceholder = (appName, appDescription) => {
            pageTitle.textContent = appName;
            pageSubtitle.textContent = '功能預覽';
            contentArea.innerHTML = createPlaceholder(appName, appDescription);
            lucide.createIcons();
        };
        document.addEventListener('DOMContentLoaded', renderDashboard);
    </script>
</body>
</html>
EOF
echo "所有檔案建立完成。"

# --- [階段 3] 安裝依賴 ---
echo "✅ [3/5] 正在使用 Poetry 安裝依賴..."
cd "$PROJECT_DIR" && poetry install --no-root > /dev/null 2>&1
echo "依賴安裝完成。"

# --- [階段 4] 啟動伺服器 ---
echo "✅ [4/5] 正在背景啟動 FastAPI 伺服器..."
# 使用 nohup 確保即使 shell 關閉，伺服器也能持續運行
nohup poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
# 等待幾秒鐘確保伺服器已完全啟動
sleep 5
echo "伺服器已在背景啟動，日誌將寫入 server.log。"

# --- [階段 5] 產生公開網址 ---
echo "✅ [5/5] 正在產生 Colab 公開存取網址..."
python -c "from google.colab import output; print('\n\n--- 部署完成 ---'); output.serve_kernel_port_as_window(8000, anchor_text='點擊這裡，在新分頁中開啟您的應用程式')"

echo -e "\n如果連結未自動顯示，請檢查 Colab 輸出。腳本執行完畢。\n"
