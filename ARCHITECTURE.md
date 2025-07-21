# 系統架構與執行模式詳解

本文檔詳細說明了本專案的系統架構、執行模式、檔案功能及所使用的技術。

## 1. 核心設計哲學：職責分離與日誌中心化

本系統的核心設計哲學是嚴格的「職責分離」。每個元件只做一件事，並把它做好。系統的狀態和歷史記錄，則由一個中心化的日誌系統（真相堡壘）來統一管理。

- **後端 (Backend)**：只負責處理業務邏輯和 API 請求。它不關心日誌如何顯示，只負責「忠實記錄」。
- **前端 (Frontend/Colab)**：只負責顯示資訊。它不直接執行業務邏輯，而是透過讀取中心化的日誌來了解系統狀態。
- **日誌系統 (Logging System)**：作為後端和前端之間的橋樑，是系統狀態的唯一真實來源。

## 2. 技術棧

- **後端**：
    - **FastAPI**: 一個現代、高效能的 Python Web 框架，用於建立 API。
    - **Uvicorn**: 一個 ASGI 伺服器，用於在生產環境中運行 FastAPI 應用。
    - **SQLite**: 一個輕量級的、無伺服器的 SQL 資料庫引擎，用於儲存日誌。
- **前端 (Colab)**：
    - **IPython/Jupyter**: Colab 的核心，提供了互動式的 Python 環境。
    - **ipywidgets**: 用於在 Colab 中建立互動式的 UI 元件（如日誌面板、狀態標籤）。
- **依賴管理**：
    - **Poetry**: 一個現代的 Python 依賴管理和打包工具。

## 3. 專案檔案結構與功能

```
.
├── ARCHITECTURE.md         # 本架構文件
├── colab_main.py           # Colab Notebook 的主進入點
├── integrated_platform/
│   ├── pyproject.toml      # Poetry 的專案設定檔
│   ├── poetry.lock         # 鎖定的依賴版本
│   ├── src/
│   │   ├── main.py         # FastAPI 應用程式的核心
│   │   ├── log_manager.py  # 日誌管理器 (LogManager)
│   │   └── display_manager.py # 智慧顯示管理器 (DisplayManager)
│   └── ...
├── logs.sqlite             # 日誌資料庫 (真相堡壘)
├── run.sh                  # 後端部署腳本 (沉默的執行者)
└── server.log              # Uvicorn 伺服器的原始輸出日誌
```

### 3.1. `run.sh`：沉默的執行者

- **職責**：準備 Python 環境並在背景啟動後端伺服器。
- **執行模式**：此腳本被設計為「完全靜默」。它不會向標準輸出或標準錯誤輸出任何資訊。所有的啟動過程都應透過日誌系統來追蹤。
- **技術細節**：
    - 使用 `set -e` 確保在任何命令失敗時立即退出。
    - 使用 `pip install poetry` 安裝 Poetry。
    - 使用 `poetry install --no-root` 安裝專案依賴。
    - 使用 `nohup ... &` 在背景啟動 Uvicorn 伺服器，並將其原始輸出重新導向到 `server.log`。

### 3.2. `integrated_platform/src/log_manager.py`：日誌管理器

- **職責**：提供一個執行緒安全的介面，用於將日誌寫入 `logs.sqlite` 資料庫。
- **執行模式**：作為一個單例（或至少在應用中作為一個共享的全域實例），供所有需要記錄日誌的模組使用。
- **技術細節**：
    - 使用 `sqlite3` 模組與資料庫互動。
    - 使用 `threading.Lock` 來保護對資料庫的寫入操作，確保在多執行緒環境（如 FastAPI）中的安全。
    - `_create_table()` 方法在 `__init__` 中被呼叫，以確保在 `LogManager` 實例化時，`logs` 表格就已經存在。
    - `log()` 方法獲取「亞洲/台北」時區的目前時間，並將其格式化為 ISO 8601 字串，然後將日誌插入資料庫。

### 3.3. `integrated_platform/src/main.py`：FastAPI 應用程式

- **職責**：提供後端的 API 端點。
- **執行模式**：由 Uvicorn 伺服器載入和運行。
- **技術細節**：
    - 建立一個全域的 `LogManager` 實例。
    - 使用 `@app.middleware("http")` 定義一個中介軟體，自動記錄所有傳入的 HTTP 請求。
    - 在每個 API 端點中，呼叫 `log_manager.log()` 來記錄詳細的業務邏輯日誌。

### 3.4. `integrated_platform/src/display_manager.py`：智慧顯示管理器

- **職責**：作為 Colab UI 的唯一「畫家」，持續從 `logs.sqlite` 讀取日誌並將其顯示出來。
- **執行模式**：在一個單獨的背景執行緒中運行，以避免阻塞 Colab 主流程。
- **技術細節**：
    - 使用 `ipywidgets` 建立一個包含日誌輸出區域和狀態標籤的垂直佈局 (`VBox`)。
    - `start()` 方法會顯示 UI 並啟動背景執行緒。
    - `_run()` 方法是背景執行緒的主循環，它會：
        1.  定期（每秒）呼叫 `_fetch_new_logs()`。
        2.  `_fetch_new_logs()` 從 `logs.sqlite` 中查詢 `id` 大於 `self.last_log_id` 的所有日誌。
        3.  如果獲取到新的日誌，就將其列印到 `self.log_output` 中，並更新 `self.last_log_id`。
    - `stop()` 方法會設定一個 `threading.Event` 來優雅地停止背景執行緒。

### 3.5. `colab_main.py`：Colab 主流程

- **職責**：協調和啟動整個系統。
- **執行模式**：作為 Colab Notebook 中第一個執行的儲存格。
- **技術細節**：
    1.  **初始化 `LogManager`**：建立 `logs.sqlite` 資料庫和 `logs` 表格。
    2.  **啟動 `DisplayManager`**：立即在背景執行緒中啟動 UI，確保介面恆定。
    3.  **記錄並執行 `run.sh`**：使用 `subprocess.Popen` 執行 `run.sh`，並即時讀取其輸出，將每一行都作為日誌寫入資料庫。這使得 `run.sh` 的執行過程可以被即時追蹤。
    4.  **模擬操作**：執行一些模擬的前端操作，並將其記錄到日誌中。
    5.  **停止 `DisplayManager`**：在所有任務完成後，停止 `DisplayManager` 的背景執行緒。

## 4. 執行流程總結

1.  **使用者** 在 Colab 中執行 `colab_main.py`。
2.  `colab_main.py` 立即：
    a. 建立 `LogManager`，確保 `logs.sqlite` 存在。
    b. 啟動 `DisplayManager`，一個穩定的 UI 介面立刻出現。
3.  `DisplayManager` 的背景執行緒開始每秒輪詢 `logs.sqlite` 以獲取新日誌。
4.  `colab_main.py` 將「正在執行 run.sh」這條日誌寫入 `logs.sqlite`。
5.  `DisplayManager` 獲取到這條日誌並顯示它。
6.  `colab_main.py` 執行 `run.sh`。`run.sh` 的所有輸出都被 `colab_main.py` 擷取並逐行寫入 `logs.sqlite`。
7.  `DisplayManager` 持續顯示 `run.sh` 的執行進度。
8.  `run.sh` 啟動 FastAPI 伺服器。
9.  FastAPI 伺服器開始處理請求，並將自己的日誌寫入 `logs.sqlite`。
10. `DisplayManager` 顯示來自 FastAPI 的日誌。
11. 所有流程結束後，`colab_main.py` 停止 `DisplayManager`。

這種架構確保了無論後端發生什麼，前端的顯示都是穩定和一致的，因為它只依賴於唯一的真相來源：`logs.sqlite`。
