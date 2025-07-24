# 系統架構說明 (v3 - 模組化藍圖架構)

本文件詳細說明了專案當前的系統架構。此架構的核心設計理念是**模組化**、**可擴展性**和**快速啟動**。

## 核心設計原則

1.  **微核心 (Microkernel)**：擁有一個極其輕量的核心伺服器 (`main.py`)，其本身不包含任何業務邏輯。它的唯一職責是發現、加載並協調各個功能模組。
2.  **可插拔應用 (Pluggable Apps)**：所有具體的業務功能都被封裝在獨立的 "App" 模組中，存放於 `apps/` 目錄下。每個 App 都是一個自包含的單元，擁有自己的路由、邏輯和依賴（未來可擴展）。
3.  **動態發現與註冊**：伺服器在啟動時會自動掃描 `apps/` 目錄，動態導入有效的 App 模組，並將其 API 路由器掛載到主應用上。這意味著新增或移除一個功能，只需要添加或刪除對應的 App 目錄即可，無需修改核心程式碼。
4.  **非同步與懶加載**：整個平台基於 `asyncio` 和 `FastAPI`，確保了高效的 I/O 處理。業務邏輯在對應的 API 被調用時才真正執行，實現了懶加載，極大地加快了初始啟動速度。
5.  **統一的 Python 腳本管理**：拋棄了複雜的 Shell 腳本，所有管理任務（安裝、執行、測試）都由統一的 Python 腳本 (`run.py`, `test.py`) 處理，簡化了開發和部署流程。

## 目錄結構詳解

```
.
├── apps/                  # 所有功能應用的根目錄
│   ├── transcriber/       # 「錄音轉寫」應用模組
│   │   ├── __init__.py
│   │   ├── main.py        # 定義此模組的 API 路由 (APIRouter) 和元數據
│   │   └── logic.py       # 實現此模組的業務邏輯
│   └── quant/             # 「量化分析」應用模組
│       ├── __init__.py
│       ├── main.py
│       └── logic.py
├── static/                # 靜態文件目錄
│   └── index.html         # 平台主歡迎頁面
├── .gitignore             # Git 忽略清單
├── ARCHITECTURE.md        # 本文件
├── Colab_Guide.md         # Colab 使用指南
├── main.py                # 核心伺服器入口點 (FastAPI 微核心)
├── README.md              # 專案主說明文件
├── requirements.txt       # Python 依賴清單
├── run.py                 # 主要的執行腳本 (安裝與啟動)
├── test.py                # 自動化整合測試腳本
└── uv_manager.py          # 使用 uv 的依賴安裝管理器
```

## 執行流程

### 1. 啟動與安裝

-   使用者執行 `python3 run.py`。
-   `run.py` 首先調用 `uv_manager.py`。
-   `uv_manager.py` 檢查並安裝 `uv`，然後使用 `uv pip install -r requirements.txt` 安裝所有必要的依賴。
-   安裝成功後，`run.py` 使用 `uvicorn` 啟動 `main:app`。

### 2. 伺服器初始化 (Lifespan)

-   `uvicorn` 啟動 `main.py` 中的 FastAPI 應用實例 `app`。
-   FastAPI 觸發 `lifespan` 非同步上下文管理器。
-   `lifespan` 函式掃描 `apps/` 目錄下的所有子目錄。
-   對於每個有效的 App 目錄（包含 `main.py`），動態導入其 `main` 模組。
-   從模組中讀取 `router` (一個 `APIRouter` 實例) 和 `app_info` (一個包含元數據的字典)。
-   使用 `app.include_router()` 將 App 的路由掛載到主應用上。
-   將 `app_info` 存入全域的 `APPS_REGISTER` 列表中。
-   伺服器完成啟動，準備好接受請求。

### 3. 前端渲染

-   使用者瀏覽器訪問根路徑 `/`。
-   FastAPI 回傳 `static/index.html` 的內容。
-   頁面加載後，其內嵌的 JavaScript 會向 `/api/apps` 發送一個非同步請求。
-   `/api/apps` 路由回傳 `APPS_REGISTER` 列表的 JSON 格式。
-   JavaScript 根據收到的數據，動態地在頁面上生成每個 App 的卡片，展示其名稱和描述。

## 如何擴展

要新增一個名為 "MyNewApp" 的新功能，只需：
1.  在 `apps/` 目錄下建立一個新目錄 `mynewapp`。
2.  在 `apps/mynewapp/` 中建立 `main.py` 和 `logic.py`。
3.  在 `apps/mynewapp/main.py` 中，定義 `app_info` 字典和 `router`（`APIRouter`），並註冊相關的 API 路由。
4.  在 `apps/mynewapp/logic.py` 中實現業務邏輯。
5.  重新啟動伺服器。新應用將會被自動發現、加載和顯示。
