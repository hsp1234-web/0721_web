# 整合式日誌驅動平台

本專案旨在建立一個以日誌為中心、前後端分離的整合式應用平台。透過將所有系統事件記錄到一個統一的日誌中心，我們得以實現高度解耦的架構，讓不同的系統元件可以獨立運作和監控。

## 核心設計哲學

本系統的核心設計哲學是嚴格的「職責分離」與「日誌中心化」。

-   **後端 (Backend)**：只負責處理業務邏輯和 API 請求，並將所有操作「忠實記錄」到日誌系統。
-   **前端 (Frontend/Colab)**：只負責顯示資訊，透過讀取中心化的日誌來了解系統狀態。
-   **日誌系統 (Logging System)**：作為後端和前端之間的橋樑，是系統狀態的唯一真實來源。

## 快速開始

1.  **安裝依賴**

    本專案使用 Poetry 進行依賴管理。首先，請確保您已安裝 Poetry。

    ```bash
    pip install poetry
    ```

2.  **啟動後端伺服器**

    執行 `run.sh` 腳本來安裝依賴並在背景啟動後端伺服器。

    ```bash
    bash run.sh
    ```

    此腳本會以靜默模式執行，所有啟動過程都會被記錄到 `logs.sqlite` 中。

3.  **啟動前端監控介面**

    在 Colab 或 Jupyter 環境中，您可以手動初始化 `DisplayManager` 來啟動前端的監控介面。

    ```python
    from integrated_platform.src.display_manager import DisplayManager
    from pathlib import Path

    # 設定日誌資料庫的路徑
    db_path = Path("../logs.sqlite")

    # 啟動顯示管理器
    display_manager = DisplayManager(db_path)
    display_manager.start()

    # 當您想停止時，可以執行：
    # display_manager.stop()
    ```

    您將會看到一個即時更新的日誌面板，顯示後端伺服器的所有活動。

## 技術棧

-   **後端**：
    -   **FastAPI**: 用於建立高效能的 API。
    -   **Uvicorn**: 用於運行 FastAPI 應用的 ASGI 伺服器。
    -   **SQLite**: 用於儲存日誌的輕量級資料庫。
-   **前端 (Colab)**：
    -   **IPython/Jupyter**: 提供互動式的 Python 環境。
    -   **ipywidgets**: 用於在 Colab 中建立互動式的 UI 元件。
-   **依賴管理**：
    -   **Poetry**: 用於管理 Python 依賴。

## 專案結構

```
.
├── ARCHITECTURE.md         # 詳細的系統架構文件
├── integrated_platform/
│   ├── README.md           # 本說明文件
│   ├── pyproject.toml      # Poetry 的專案設定檔
│   ├── src/
│   │   ├── main.py         # FastAPI 應用程式核心
│   │   ├── log_manager.py  # 日誌管理器
│   │   └── display_manager.py # 前端顯示管理器
│   └── ...
├── logs.sqlite             # 日誌資料庫
├── run.sh                  # 後端部署腳本
└── server.log              # Uvicorn 伺服器的原始輸出日誌
```

## 系統能力清單 (Capabilities)

此處記錄了所有可用的後勤與特種作戰指令。

### 1. 驗證控制台

此指令用於檢查 `commander_console.py` 是否能正常啟動。

**指令:**

```bash
poetry run python src/commander_console.py hello
```
