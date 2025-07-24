# 模組化非同步平台 (Modular Async Platform)

[![架構](https://img.shields.io/badge/架構-模組化微核心-blueviolet)](ARCHITECTURE.md)
[![測試狀態](https://img.shields.io/badge/測試-全部通過-brightgreen)](test.py)

歡迎來到模組化非同步平台！這是一個基於 FastAPI 的高效能 Web 應用框架，其核心設計理念是**模組化**、**可擴展性**和**極速啟動**。

## 專案特色

-   **可插拔應用架構**：所有功能都是獨立的 "App"，存放在 `apps/` 目錄下。新增或移除功能只需增刪目錄，無需修改核心程式碼。
-   **動態應用發現**：伺服器啟動時自動掃描、加載並註冊所有可用的應用。
-   **非同步與懶加載**：基於 `asyncio` 和 `FastAPI`，確保 I/O 高效。業務邏輯懶加載，加快了伺服器的初始啟動速度。
-   **統一的 Python 腳本管理**：使用 `run.py` 進行安裝和啟動，使用 `test.py` 進行自動化整合測試。
-   **現代化依賴管理**：使用 `venv` + `uv` + `requirements.txt` 進行輕量級、高速的環境管理。
-   **Colab 友好**：透過 `colab_run.py`，只需一行 `import` 即可在 Google Colab 中一鍵部署和啟動。

詳細的技術細節請參閱 [**系統架構說明 (ARCHITECTURE.md)**](ARCHITECTURE.md)。

## 快速開始

### 環境要求
- Python 3.9+

### 本地端設定與啟動

1.  **複製專案**
    ```bash
    git clone [您的專案 GitHub URL]
    cd [您的專案目錄名稱]
    ```

2.  **建立虛擬環境 (建議)**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # 在 Windows 上使用 `venv\Scripts\activate`
    ```

3.  **安裝與啟動**
    在專案根目錄下，執行以下指令：
    ```bash
    python3 run.py
    ```
    此指令會自動完成兩件事：
    - **安裝依賴**：調用 `uv_manager.py` 安裝 `requirements.txt` 中的所有套件。
    - **啟動伺服器**：在 `http://0.0.0.0:8000` 啟動 FastAPI 伺服器。

    您現在可以打開瀏覽器訪問 `http://127.0.0.1:8000` 來查看平台主頁。

### 在 Colab 中使用

請參閱詳細的 [**Colab 使用指南 (Colab_Guide.md)**](Colab_Guide.md)。

## 開發

### 新增一個應用

1.  在 `apps/` 目錄下建立一個新的子目錄，例如 `apps/mynewapp`。
2.  在該目錄下建立 `main.py` 和 `logic.py`。
3.  參考 `apps/transcriber/main.py` 的結構，在 `main.py` 中定義 `app_info` 字典和 `router` (APIRouter)。
4.  將您的業務邏輯放在 `logic.py` 中。
5.  重新啟動伺服器，您的新應用將被自動加載。

### 執行測試

本專案包含一個整合測試腳本，可以驗證整個應用的生命週期。
```bash
python3 test.py
```
此腳本會自動：
1.  安裝所有依賴。
2.  在一個不常用的埠號上啟動伺服器。
3.  測試 API 是否能正常回傳應用列表。
4.  測試伺服器是否能被優雅地關閉。

這確保了程式碼的穩定性和可靠性。
