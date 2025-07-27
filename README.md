# 新一代整合服務平台

本專案旨在將多個獨立的業務邏輯模組，整合到一個統一、穩定且高效能的 API 服務平台中。

## 核心架構

- **框架**: `FastAPI` (非同步)
- **環境管理**: `venv` + `uv`
- **核心特色**:
  - **啟動時環境檢查**: 在伺服器啟動前，會自動檢查磁碟空間和記憶體使用率，確保系統處於健康狀態。
  - **模組化業務邏輯**: 每個核心功能（如 MP3 轉寫、金融分析）都被設計為獨立的模組。
  - **背景任務處理**: 能夠觸發並監控長時間執行的背景任務，並將日誌記錄到檔案中。

## 已整合功能

### 1. MP3 轉寫服務

- **功能**: 提供檔案上傳和狀態查詢的 API，模擬非同步的轉寫流程。
- **端點**:
  - `POST /upload`: 上傳一個音檔，開始轉寫任務。
  - `GET /status/{task_id}`: 查詢指定任務的狀態和結果。

### 2. 金融數據分析服務 (觸發機制)

- **功能**: 提供一個 API 來觸發重量級的、離線的金融數據工程管線 (`build-feature-store`)。
- **端點**:
  - `POST /analysis/build`: 在背景啟動 `build-feature-store` 任務。
  - `GET /analysis/status/{task_id}`: 查詢指定分析任務的狀態。
- **注意**: 由於沙盒環境的限制，背景任務的 Python 環境未能成功設定，導致任務本身執行失敗。但觸發、監控和日誌記錄的機制已完全建立。

## 如何設定與執行

1.  **建立虛擬環境**:
    ```bash
    python3 -m venv .venv
    ```

2.  **安裝依賴**:
    我們使用 `uv` 來加速依賴安裝。
    ```bash
    # 先安裝 uv
    .venv/bin/pip install uv

    # 一次性安裝所有依賴
    .venv/bin/uv pip install fastapi "uvicorn[standard]" psutil aiosqlite duckdb typer pandas fredapi yfinance aiofiles requests-cache vectorbt deap python-multipart
    ```

3.  **啟動伺服器**:
    ```bash
    .venv/bin/uvicorn main_api:app --host 0.0.0.0 --port 8000
    ```
    伺服器將在 `http://localhost:8000` 上運行。

## API 端點測試範例

- **健康檢查**:
  ```bash
  curl http://localhost:8000/health
  ```

- **上傳檔案**:
  ```bash
  echo "fake data" > test.mp3
  curl -X POST -F "file=@test.mp3" http://localhost:8000/upload
  ```

- **觸發金融分析**:
  ```bash
  curl -X POST http://localhost:8000/analysis/build
  ```

---
*本文件由 AI 助手順利產生*
