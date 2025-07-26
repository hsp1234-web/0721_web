# 鳳凰之心 - 模組化 Web 應用框架

這是一個基於 Python 的現代後端應用程式框架範例，旨在展示如何建構一個高效能、可擴展、可維護的系統。它整合了多項現代軟體工程的最佳實踐。

## ✨ 核心功能

- **模組化應用架構**: 在 `apps` 目錄下，每個子目錄都是一個獨立的功能模組 (例如 `quant`, `transcriber`)，擁有自己的路由和邏輯。
- **統一日誌系統**: 使用 `core/logging_config.py` 提供的標準化日誌設定，支援純文字和 Markdown 格式輸出。
- **單一應用入口**: 所有功能都透過 `server_main.py` 中的主 FastAPI 應用程式啟動和管理。
- **資源懶加載 (Lazy Loading)**：透過範例 `apps/transcriber` 展示了如何在首次 API 請求時才加載大型資源（如 AI 模型），大幅縮短了服務的初始啟動時間。
- **分層的依賴管理**：使用 `requirements/` 目錄下的 `base.txt`, `dev.txt`, `colab.txt` 對不同環境的依賴進行了清晰的劃分。
- **完善的測試與品質保證**：
  - 整合 `pytest` 進行單元測試與整合測試。
  - 使用 `e2e_test.sh` 進行端到端測試。
  - 透過 `pre-commit` 框架整合了 `ruff` 等工具，在程式碼提交前自動進行風格檢查。
- **Colab/Jupyter 整合**：包含一個 `run.py`，它可以在 Colab 儲存格中啟動一個純文字的儀表板，即時渲染系統狀態、資源使用率和日誌。

## 🚀 如何開始

### 1. 環境設定

建議使用 Python 3.8+。首先，執行設定腳本來建立虛擬環境並安裝所有依賴：

```bash
./setup.sh
```

### 2. 啟動應用程式

若要啟動 FastAPI 伺服器，請執行：

```bash
python server_main.py
```

伺服器將在 `http://127.0.0.1:8000` 上啟動。

### 3. 在 Colab 中執行

若要在 Colab 或 Jupyter 環境中啟動監控儀表板，請執行：

```python
import run
run.display_dashboard()
```

### 4. 運行測試

本專案提供了端到端測試腳本：

```bash
./e2e_test.sh
```

這會啟動一個測試伺服器，並對所有 API 端點進行測試。

## 📂 專案結構

```
.
├── ARCHITECTURE.md     # 詳細的架構設計文檔
├── README.md           # 就是你正在看的這個檔案
├── apps/               # 業務邏輯單元 (Apps)
│   ├── quant/          # 量化分析 App
│   └── transcriber/    # 語音轉錄 App
├── core/               # 核心模組
│   ├── config.py
│   ├── logging_config.py
│   ├── monitor.py
│   └── presentation_manager.py
├── requirements/       # 分層的依賴管理
│   ├── base.txt
│   ├── colab.txt
│   └── dev.txt
├── run.py              # Colab 環境啟動器與儀表板
├── server_main.py      # FastAPI 應用主入口
├── setup.sh            # 設定腳本
├── e2e_test.sh         # 端到端測試腳本
├── templates/          # HTML 模板
├── tests/              # 自動化測試目錄
└── pyproject.toml      # 專案元數據與工具配置
```
