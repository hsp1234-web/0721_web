# 高效能 Web 應用程式框架

這是一個基於 Python 的現代後端應用程式框架範例，旨在展示如何建構一個高效能、可擴展、可維護的系統。它整合了多項現代軟體工程的最佳實踐。

## ✨ 核心功能

- **進程級模組化架構**：使用 `multiprocessing` 和 `subprocess` 將核心服務（Web 應用、日誌系統、監控）隔離在獨立的進程中，確保穩定性與資源隔離。
- **非同步日誌系統**：所有日誌（應用日誌、系統指標）都透過一個非阻塞的佇列 (`Queue`) 發送到一個專門的寫入進程，該進程使用 `DuckDB` 進行高效的批次寫入，避免了日誌記錄成為應用效能的瓶頸。
- **動態 API 路由**：主應用程式 (`main.py`) 在啟動時會自動掃描 `apps/` 目錄，並加載所有符合規範的子應用路由。新增功能模組無需修改主程式碼，實現真正的「即插即用」。
- **資源懶加載 (Lazy Loading)**：透過範例 `apps/transcriber` 展示了如何在首次 API 請求時才加載大型資源（如 AI 模型），大幅縮短了服務的初始啟動時間。
- **分層的依賴管理**：使用 `requirements/` 目錄下的 `base.txt`, `dev.txt`, `colab.txt` 對不同環境的依賴進行了清晰的劃分。
- **完善的測試與品質保證**：
  - 整合 `pytest` 進行單元測試與整合測試。
  - 使用 `pytest-cov` 生成測試覆蓋率報告。
  - 透過 `pre-commit` 框架整合了 `ruff`, `mypy`, `bandit` 等工具，在程式碼提交前自動進行風格檢查、靜態型別分析和安全掃描。
- **生產級啟動腳本**：提供了 `start.sh`，支持以後台守護進程模式啟動、停止、重啟和查看日誌，簡化了部署流程。
- **Colab/Jupyter 整合**：包含了 `colab_run.py` 和 `colab_display.py`，作為在 Notebook 環境中啟動和監控後端服務的橋樑。

## 🚀 如何開始

### 1. 環境設定

建議使用 Python 3.8+。首先，建立並啟用虛擬環境：

```bash
python -m venv .venv
source .venv/bin/activate
```

接著，安裝所有開發所需的依賴。我們推薦使用 `uv`，一個極速的 Python 套件安裝器。

```bash
# 安裝 uv (如果尚未安裝)
pip install uv

# 使用 uv 安裝所有開發依賴
uv pip sync requirements/dev.txt
```

### 2. 啟動應用程式

你可以使用為生產環境設計的 `start.sh` 腳本來管理應用。

- **在前台啟動 (用於開發與除錯):**
  ```bash
  ./start.sh
  ```
  日誌會直接輸出到你的終端。按下 `Ctrl+C` 來停止。

- **在後台啟動 (用於部署):**
  ```bash
  ./start.sh -d
  ```

- **其他管理指令:**
  ```bash
  ./start.sh status    # 檢查後台應用狀態
  ./start.sh logs      # 實時查看後台日誌
  ./start.sh stop      # 停止後台運行的應用
  ./start.sh restart   # 重啟後台應用
  ```

### 3. 運行測試

本專案提供了兩種測試模式：

- **快速功能測試 (Quick Test):**
  只運行核心的功能性測試，速度快，適合在開發過程中頻繁使用。
  ```bash
  python testq.py
  ```

- **完整品質檢查與測試 (Full Test):**
  這會執行 `pre-commit` 的所有靜態分析（程式碼風格、型別、安全），然後再運行功能測試並生成覆蓋率報告。這是提交前或在 CI/CD 環境中應使用的指令。
  ```bash
  python test.py
  ```
  *(注意：首次運行 `test.py` 可能會因為 `pre-commit` 安裝環境而稍慢)*

### 4. 使用 API 範例

當服務啟動後，你可以使用 `curl` 或任何 HTTP 客戶端來與其互動。以下是呼叫語音轉錄服務的範例：

```bash
# 建立一個假的音訊檔案
echo "這是一個模擬的音訊內容" > fake_audio.mp3

# 發送 API 請求
curl -X POST -F "file=@fake_audio.mp3;type=audio/mpeg" http://127.0.0.1:8000/transcriber/upload
```

- **第一次**呼叫此 API 會比較慢（約 5-6 秒），因為後端正在「懶加載」AI 模型。
- **後續所有**的呼叫都會非常快（約 1 秒），因為模型已經被快取在記憶體中。

你也可以在瀏覽器中開啟 `http://127.0.0.1:8000/docs` 來查看由 FastAPI 自動生成的互動式 API 文件。

## 📂 專案結構

```
.
├── ARCHITECTURE.md     # 詳細的架構設計文檔
├── README.md           # 就是你正在看的這個檔案
├── apps/               # 業務邏輯單元 (Apps)
│   ├── transcriber/    # 語音轉錄 App 範例
│   └── ...             # 其他 App
├── core.py             # 系統總指揮官，管理所有進程
├── colab_run.py        # Colab 環境啟動器
├── colab_display.py    # Colab 環境顯示介面
├── database/           # DuckDB 資料庫檔案存放處
├── logger/             # 非同步日誌系統模組
├── main.py             # FastAPI 應用主入口，負責路由聚合
├── requirements/       # 分層的依賴管理
│   ├── base.txt
│   ├── colab.txt
│   └── dev.txt
├── run.py              # Uvicorn 伺服器啟動器
├── start.sh            # 生產環境啟動腳本
├── static/             # 靜態檔案目錄
├── tests/              # 自動化測試目錄
│   ├── test_app_transcriber.py
│   └── test_logger.py
├── test.py             # 完整測試啟動器
├── testq.py            # 快速測試啟動器
├── uv_manager.py       # uv 套件管理器
├── .pre-commit-config.yaml # Pre-commit 品質預檢設定
└── pyproject.toml      # 專案元數據與工具配置
```

## 🛡️ 品質保證

本專案使用 `pre-commit` 框架來確保所有提交的程式碼都符合一定的品質標準。當你設定好環境 (`pre-commit install`) 後，每次 `git commit` 都會自動觸發以下檢查：

- **Ruff**: 執行超快速的程式碼 Linter 和 Formatter。
- **MyPy**: 進行靜態型別檢查，減少運行時錯誤。
- **Bandit**: 掃描程式碼，尋找常見的安全漏洞。

這個機制能夠極大地提升程式碼的健壯性和團隊協作的一致性。
