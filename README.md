# 鳳凰之心 Web 應用程式框架

這是一個基於 Python 的現代後端應用程式框架，旨在展示如何建構一個高效能、可擴展、可維護的系統。它整合了多項現代軟體工程的最佳實踐。

## ✨ 核心功能

- **模組化架構**：將核心服務（Web 應用、日誌系統、監控）隔離在獨立的模組中，確保穩定性與資源隔離。
- **非同步日誌系統**：所有日誌都透過一個非阻塞的佇列發送到一個專門的寫入程序，避免了日誌記錄成為應用效能的瓶頸。
- **動態 API 路由**：主應用程式 (`main.py`) 在啟動時會自動掃描 `apps/` 目錄，並加載所有符合規範的子應用路由。新增功能模組無需修改主程式碼，實現真正的「即插即用」。
- **分層的依賴管理**：使用 `requirements.txt` 對不同環境的依賴進行了清晰的劃分。
- **Colab/Jupyter 整合**：包含一個強大的 `colab_run.py`，它不僅是 Colab 的啟動橋樑，更內建了一個純文字、多區塊的儀表板，可在 Colab 儲存格中即時渲染系統狀態、資源使用率和日誌，提供卓越的監控體驗。

## 📂 專案結構

```
.
├── WEB/
│   ├── docs/
│   │   ├── ARCHITECTURE.md
│   │   ├── Colab_Guide.md
│   │   └── TEST.md
│   │
│   ├── apps/
│   │   ├── __init__.py
│   │   ├── logger/
│   │   ├── transcriber/
│   │   └── quant/
│   │
│   ├── templates/
│   │   └── dashboard.html
│   │
│   ├── README.md
│   ├── colab_run.py
│   ├── main.py
│   └── requirements.txt
```

## 🚀 如何開始

請參考 `WEB/docs/Colab_Guide.md` 中的說明，在 Colab 環境中啟動專案。
