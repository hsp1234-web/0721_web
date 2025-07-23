# 鳳凰之心作戰平台 v2.1.0

## 專案簡介

「鳳凰之心」是一個專為在 Google Colab 環境中穩定、可靠地運行 Web 服務而設計的框架。它採用了「單線程堡壘」架構，旨在解決 Colab 環境中常見的日誌丟失、啟動不穩定等問題。

本專案的核心目標是提供一個**絕對可靠的部署與監控體驗**。

## 核心設計哲學

本系統的核心設計哲學是**絕對可靠的順序執行**。我們相信，在資源受限且行為特殊的 Colab 環境中，最簡單、最線性的流程就是最穩定的流程。

-   **單一啟動入口**: 所有操作都由 `colab_run.py` 統一協調。
-   **阻塞式依賴安裝**: 在執行任何服務之前，主線程會阻塞並等待所有 `pip` 依賴安裝完成，確保環境的完整性。
-   **日誌優先**: 日誌顯示系統是除安裝外，第一個被啟動的元件，確保能捕獲後續所有的啟動與運行日誌。
-   **健康檢查**: 在對外暴露服務之前，會嚴格執行健康檢查，確保後端服務已完全就緒。

## 快速開始

本專案被設計為直接在 Google Colab 中使用。您不需要在本機上進行複雜的設定。

1.  **準備您的專案**
    *   將您的 FastAPI 或其他 Web 應用程式碼放入 `integrated_platform/src` 或其子目錄中。
    *   在 `requirements.txt` 中添加您的 Python 依賴。

2.  **在 Colab 中啟動**
    *   上傳您的整個專案資料夾（例如，名為 `WEB`）到 Google Drive，或直接 `git clone` 到 Colab 環境的 `/content/WEB` 路徑下。
    *   使用我們在 `Colab_Guide.md` 中提供的儲存格範本。將其貼到 Colab 儲存格中並執行。

    平台將會自動完成以下所有步驟：
    1.  安裝 `requirements.txt` 中定義的所有依賴。
    2.  啟動一個包含即時日誌和系統狀態的監控儀表板。
    3.  在背景啟動您的 FastAPI 後端服務。
    4.  確認您的服務已健康運行。
    5.  生成一個公開的 `ngrok`-like 連結，供您從外部訪問。

詳細的使用說明和可直接複製的儲存格程式碼，請參閱 [Colab_Guide.md](./Colab_Guide.md)。

## 技術棧

-   **後端框架**: FastAPI
-   **ASGI 伺服器**: Uvicorn
-   **核心架構**:
    -   使用原生 `subprocess` 進行阻塞式安裝。
    -   使用原生 `threading` 進行背景任務管理 (日誌、後端服務)。
-   **前端 (Colab)**:
    -   `IPython.display` 用於渲染 HTML 和 Javascript，構建動態儀表板。
    -   `google.colab.output` 用於建立公開服務連結。
-   **日誌系統**: 原生 `sqlite3`，提供一個輕量、可靠的持久化日誌儲存。

## 專案結構

```
.
├── ARCHITECTURE.md             # 詳細的「單線程堡壘」架構說明
├── Colab_Guide.md              # Google Colab 使用者指南與儲存格範本
├── README.md                   # 本說明文件
├── colab_run.py                # 唯一的啟動入口與總指揮
├── integrated_platform/
│   └── src/
│       ├── main.py             # FastAPI 應用程式的核心
│       └── ...                 # 其他後端業務邏輯
├── requirements.txt            # Python 依賴列表
├── run.sh                      # 依賴安裝腳本 (由 colab_run.py 呼叫)
└── test.sh                     # 端對端整合測試腳本
```
