#!/bin/bash

# 【磐石協議 v2.0：Colab 自動化測試與部署腳本】
# 本腳本將建立一個包含單元測試的完整應用，並在部署前執行品質檢查。
# 任何指令失敗都會立即中止腳本。
set -e

# --- [階段 1] 環境設定 ---
echo "✅ [1/6] 正在設定環境..."
pip install poetry > /dev/null 2>&1
export PATH="/root/.local/bin:$PATH"
echo "Poetry 已安裝並設定。"

# --- [階段 2] 建立專案結構與檔案 ---
PROJECT_DIR="integrated_platform"
echo "✅ [2/6] 正在建立專案結構..."
mkdir -p "$PROJECT_DIR/src/static"
mkdir -p "$PROJECT_DIR/tests"

# --- [階段 3] 寫入所有程式碼與設定檔 ---
echo "✅ [3/6] 正在寫入所有檔案..."

# 寫入 pyproject.toml (包含測試依賴與路徑設定)
cat > "$PROJECT_DIR/pyproject.toml" << 'EOF'
[tool.poetry]
name = "integrated-platform"
version = "0.2.0"
description = "API-driven dynamic frontend with automated testing"
authors = ["Commander"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.9"
fastapi = "*"
uvicorn = {extras = ["standard"], version = "*"}

# 將測試工具定義為開發依賴 (dev-dependencies)
[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
httpx = "^0.23.0" # FastAPI 推薦的測試用 HTTP client

# 告知 pytest 在 src 目錄下尋找原始碼，解決導入問題
[tool.pytest.ini_options]
pythonpath = ["src"]
EOF

# 寫入 src/main.py (後端業務邏輯)
cat > "$PROJECT_DIR/src/main.py" << 'EOF'
from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse
import os
import time

app = FastAPI(title="整合型應用平台")

current_dir = os.path.dirname(os.path.abspath(__file__))
static_path = os.path.join(current_dir, "static")

@app.get("/", response_class=HTMLResponse)
async def read_root():
    html_file_path = os.path.join(static_path, "index.html")
    try:
        with open(html_file_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read(), status_code=200)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>錯誤：找不到前端檔案 (index.html)</h1>", status_code=404)

@app.get("/api/apps")
async def get_applications():
    return [
        {"id": "transcribe", "name": "錄音轉寫服務", "icon": "mic", "description": "上傳音訊檔案，自動轉換為文字稿。"},
        {"id": "quant", "name": "量化研究框架", "icon": "bar-chart-3", "description": "執行金融策略回測與數據分析。"},
    ]

@app.post("/api/transcribe/upload")
async def upload_audio_for_transcription(audio_file: UploadFile = File(...)):
    time.sleep(1) # 模擬處理延遲
    return {
        "filename": audio_file.filename,
        "content_type": audio_file.content_type,
        "transcription": f"這是一段針對 '{audio_file.filename}' 的模擬語音轉寫結果。實際的 AI 模型尚未整合。"
    }
EOF

# 寫入 src/static/index.html (前端介面)
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
        const createCard = (app) => `<div class="bg-white rounded-xl shadow-md overflow-hidden hover:shadow-lg hover:-translate-y-1 transition-all duration-300 cursor-pointer" onclick="routeToApp('${app.id}', '${app.name}', '${app.description}')"><div class="p-6"><div class="flex items-center space-x-4"><div class="flex-shrink-0"><div class="w-12 h-12 bg-indigo-500 text-white rounded-lg flex items-center justify-center"><i data-lucide="${app.icon}"></i></div></div><div><div class="text-xl font-medium text-black">${app.name}</div><p class="text-slate-500">${app.description}</p></div></div></div></div>`;
        const createGenericPlaceholder = (appName, appDescription) => `<div class="bg-white p-8 rounded-xl shadow-md"><button onclick="renderDashboard()" class="flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-semibold mb-6"><i data-lucide="arrow-left" class="w-4 h-4 mr-2"></i>返回儀表板</button><h2 class="text-2xl font-bold mb-2">${appName}</h2><p class="text-slate-600 mb-6">${appDescription}</p><div class="border-t border-slate-200 pt-6"><h3 class="font-semibold mb-4">功能佔位符</h3><div class="bg-slate-50 p-6 rounded-lg text-center text-slate-500"><p>此處將會是「${appName}」的實際操作介面。</p></div></div></div>`;
        const createTranscribeUI = () => `<div><button onclick="renderDashboard()" class="flex items-center text-sm text-indigo-600 hover:text-indigo-800 font-semibold mb-6"><i data-lucide="arrow-left" class="w-4 h-4 mr-2"></i>返回儀表板</button><div class="border-b pb-6 mb-6"><h3 class="font-semibold mb-2">1. 選擇音訊檔案</h3><input type="file" id="audio-file-input" accept="audio/*" class="block w-full text-sm text-slate-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-indigo-50 file:text-indigo-700 hover:file:bg-indigo-100"/><button onclick="handleFileUpload()" class="mt-4 bg-indigo-600 text-white font-bold py-2 px-4 rounded-lg hover:bg-indigo-700 transition-colors">上傳並開始轉寫</button></div><div><h3 class="font-semibold mb-2">2. 處理狀態與結果</h3><div id="status-area" class="text-slate-500 mb-4">請上傳檔案...</div><textarea id="result-textarea" class="w-full h-48 p-2 border rounded-md bg-slate-50" readonly placeholder="轉寫結果將顯示於此..."></textarea></div></div>`;
        const handleFileUpload = async () => {
            const fileInput = document.getElementById('audio-file-input');
            const statusArea = document.getElementById('status-area');
            const resultTextarea = document.getElementById('result-textarea');
            if (!fileInput.files.length) { statusArea.textContent = '錯誤：請先選擇一個檔案。'; return; }
            const file = fileInput.files[0];
            const formData = new FormData();
            formData.append('audio_file', file);
            statusArea.textContent = '上傳中，請稍候...';
            resultTextarea.value = '';
            try {
                const response = await fetch('/api/transcribe/upload', { method: 'POST', body: formData });
                if (!response.ok) throw new Error('上傳失敗，伺服器錯誤。');
                statusArea.textContent = '處理中，模擬 AI 運算...';
                const result = await response.json();
                statusArea.textContent = '轉寫完成！';
                resultTextarea.value = result.transcription;
            } catch (error) { statusArea.textContent = \`錯誤：\${error.message}\`; }
        };
        const routeToApp = (appId, appName, appDescription) => {
            pageTitle.textContent = appName;
            pageSubtitle.textContent = appDescription;
            if (appId === 'transcribe') { contentArea.innerHTML = createTranscribeUI(); }
            else { contentArea.innerHTML = createGenericPlaceholder(appName, appDescription); }
            lucide.createIcons();
        };
        const renderDashboard = async () => {
            pageTitle.textContent = '應用程式儀表板';
            pageSubtitle.textContent = '請選擇一項服務以繼續';
            contentArea.innerHTML = '<p class="text-slate-500">正在從後端載入功能列表...</p>';
            try {
                const response = await fetch('/api/apps');
                if (!response.ok) throw new Error(\`無法取得應用程式列表 (HTTP \${response.status})\`);
                const apps = await response.json();
                contentArea.innerHTML = \`<div class="grid grid-cols-1 md:grid-cols-2 gap-6">\${apps.map(createCard).join('')}</div>\`;
            } catch (error) { contentArea.innerHTML = \`<p class="text-red-600 font-semibold">錯誤: \${error.message}</p>\`; }
            finally { lucide.createIcons(); }
        };
        document.addEventListener('DOMContentLoaded', renderDashboard);
    </script>
</body>
</html>
EOF

# 寫入 tests/test_main.py (單元測試)
cat > "$PROJECT_DIR/tests/test_main.py" << 'EOF'
from fastapi.testclient import TestClient
from main import app # 從 src/main.py 導入 app
import io

# 建立一個測試客戶端
client = TestClient(app)

def test_read_root():
    """測試根目錄 (/) 是否成功回傳 HTML。"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "應用程式儀表板" in response.text

def test_get_applications():
    """測試 /api/apps 是否回傳正確的 JSON 結構與內容。"""
    response = client.get("/api/apps")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2 # 確保至少有兩個應用
    # 檢查第一個應用的鍵是否存在
    assert "id" in data[0]
    assert "name" in data[0]
    assert "icon" in data[0]
    assert "description" in data[0]

def test_upload_transcription_file():
    """測試檔案上傳與模擬轉寫功能。"""
    # 建立一個假的記憶體內檔案
    fake_audio_content = b"this is a fake audio file content"
    fake_file = ("test_audio.mp3", io.BytesIO(fake_audio_content), "audio/mpeg")

    response = client.post(
        "/api/transcribe/upload",
        files={"audio_file": fake_file}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test_audio.mp3"
    assert "模擬語音轉寫結果" in data["transcription"]
EOF

echo "所有檔案建立完成。"

# --- [階段 4] 安裝依賴 ---
echo "✅ [4/6] 正在使用 Poetry 安裝所有依賴 (包含開發工具)..."
cd "$PROJECT_DIR" && poetry install --no-root > /dev/null 2>&1
echo "依賴安裝完成。"

# --- [階段 5] 執行單元測試 (品質閘門) ---
echo "✅ [5/6] 正在執行品質檢查 (單元測試)..."
# 使用 -v (verbose) 模式顯示詳細測試結果
poetry run pytest -v

echo "所有測試已通過！準備部署。"

# --- [階段 6] 啟動伺服器並產生網址 ---
echo "✅ [6/6] 正在啟動伺服器並產生公開網址..."
# 使用 nohup 確保伺服器在背景持續運行
nohup poetry run uvicorn src.main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
sleep 5 # 等待伺服器完全啟動

# 使用 Python 產生 Colab 的公開網址
python -c "from google.colab import output; print('\n\n--- 部署完成 ---'); output.serve_kernel_port_as_window(8000, anchor_text='點擊這裡，在新分頁中開啟您的應用程式')"

echo -e "\n如果連結未自動顯示，請檢查 Colab 輸出。腳本執行完畢。\n"
