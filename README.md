# 🚀 鳳凰之心 (Phoenix Heart) 專案 v11 - 智慧型系統 🚀

歡迎來到鳳凰之心，一個從單體架構中浴火重生的現代化微服務專案。本專案現已進化至 v11，搭載了完整的**智慧型資源管理與部署系統**，並特別為 Google Colab 環境進行了深度優化。

它不僅是一個展示微服務化的範例，更是一個具備高度穩定性、資源感知與自動化能力的專業開發框架。

---

## 一、 核心理念與工具 (Core Philosophy & Tools)

我們的架構基於以下四大核心理念：

- **微服務架構 (Microservices)**: 每個 App (`quant`, `transcriber`) 都是一個獨立、可自行運行的 FastAPI 服務。
- **完全隔離 (Total Isolation)**: 每個 App 擁有自己獨立的虛擬環境，由主啟動腳本自動管理，彼此絕不干擾。
- **聲明式環境 (Declarative Environments)**: 每個 App 的依賴由其自己的 `requirements.txt` 精確聲明。
- **智慧型資源管理 (Intelligent Resource Management)**: 在安裝**每一個**套件前，系統都會即時檢查記憶體與磁碟資源，確保不會因資源耗盡而中斷，並將所有操作記錄在案。

### 核心工具鏈:

- **`scripts/`**: **主要腳本與工具目錄**。
  - **`phoenix_starter.py` (推薦)**: 專案的**視覺化啟動器**。一鍵完成資源檢查、智慧型安裝、執行測試，並提供精美的儀表板全程監控。
  - **`launch.py`**: **核心啟動腳本 (預設快速模式)**。這是專案的唯一入口點。預設情況下，它會以快速測試模式運行，在幾秒鐘內驗證 TUI 和日誌系統。使用 `--full` 旗標可觸發完整安裝和服務啟動。
  - **`smart_e2e_test.py`**: 新一代**智能測試指揮官 (Python版)**。它以平行化的方式執行所有端對端測試，並整合了 `pytest-xdist` 和 `pytest-timeout` 來實現快速、穩健的測試。
- **`core_utils/`**: 核心工具模組，包含 `safe_installer.py` (安全安裝器) 和 `resource_monitor.py` (資源監控器)。
- **`config/resource_settings.yml`**: **全域資源設定中心**。
- **`logs/`**: **日誌中心**，所有安裝與啟動過程的詳細日誌都儲存在此。
- **uv**: 我們唯一的環境管理與安裝工具，由安全安裝模組在底層呼叫。
- **FastAPI**: 我們所有微服務使用的現代、高效能 Web 框架。

### v18+ 新增亮點：

- **模組化與視覺化報告系統**:
  - **獨立報告插件**: 報告系統已完全模組化為 `scripts/generate_report.py`，與主程序解耦，可獨立執行與測試。
  - **文字趨勢圖**: 效能報告中新增了 CPU 與 RAM 使用率的文字走勢圖 (`sparklines`)，讓效能趨勢一目了然。
  - **自動瓶頸分析**: 摘要報告現在能透過事件分析，自動列出耗時最長的任務 Top 5，幫助開發者快速定位效能瓶頸。
- **可客製化的 Colab 儀表板**:
  - **日誌等級篩選**: 您現在可以透過勾選方塊，只看您感興趣的日誌等級 (例如只看 `SUCCESS` 和 `ERROR`)。
  - **獨立效能監控頻率**: 系統資源 (CPU/RAM) 的更新頻率可以獨立設定，實現更即時的監控。
- **依賴鎖定與掃描**:
  - **`pip-tools` 整合**: 所有 `requirements.txt` 現在都由 `pip-compile` 生成，確保了依賴版本的精確鎖定，提升了環境的可重現性。
  - **自動化弱點掃描**: 透過整合 `pip-audit`，`scripts/smart_e2e_test.py` 現在會在測試流程中自動掃描已知的安全漏洞。

---

## 二、 如何開始 (Getting Started)

### 2.1. 視覺化啟動與測試 (推薦)

在任何支持 Python 的環境中，只需一個命令即可啟動鳳凰之心視覺化啟動器：

```bash
python scripts/phoenix_starter.py
```

這個命令會自動為您完成**所有事情**，並在一個精美的儀表板上顯示所有進度。

### 2.2. 快速啟動與完整部署 (推薦)

`scripts/launch.py` 是專案的**主要入口點**，提供兩種模式：

**1. 快速驗證 (預設行為)**

直接執行 `scripts/launch.py`，無需任何參數。它將在幾秒鐘內啟動 TUI 並完成一次模擬運行，非常適合快速檢查介面和日誌功能。

```bash
# 快速驗證 TUI 和日誌系統
python scripts/launch.py
```

**2. 完整部署**

當您需要安裝所有依賴並實際啟動後端服務時，請使用 `--full` 旗標。

```bash
# 執行完整的安裝和服務啟動
python scripts/launch.py --full
```

---

## 三、 Google Colab 使用指南

在 Colab 環境中，直接使用 `scripts/launch.py` 即可獲得最佳化的體驗。

- **快速驗證 (預設)**：在 Colab 儲存格中執行 `!python scripts/launch.py`，可以立即看到 TUI 儀表板的渲染效果。
- **完整執行**：執行 `!python scripts/launch.py --full` 來觸發完整的應用安裝和啟動流程。
- **V4 原生 TUI 架構**：`scripts/launch.py` 會直接在 Colab 的輸出儲存格中渲染一個高效、穩定的雙區塊儀表板，無需任何額外設定。

---

## 五、 開發與測試 (Development & Testing)

為了確保開發環境的一致性並簡化測試流程，本專案提供了一個專門用於開發和測試的依賴檔案。

### 設定測試環境

在您開始進行開發或希望執行本專案的測試套件之前，請先安裝所有必要的開發依賴。這可以透過根目錄下的 `requirements-dev.txt` 檔案一鍵完成：

```bash
# 安裝所有開發與測試所需的依賴
pip install -r requirements-dev.txt
```

這個命令會安裝 `pytest` 及其相關插件，以及所有測試案例需要的函式庫。

### 執行測試

當您的開發環境設定完成後，您可以隨時執行完整的測試套件來驗證程式碼的正確性。推薦使用我們提供的智能測試腳本：

```bash
# 執行所有測試 (推薦方式)
python scripts/smart_e2e_test.py
```

---

## 六、 檔案結構總覽 (v18 - 重構版)

以下是專案經過重構後的高層次檔案結構。更詳細的架構藍圖、設計哲學及每個模組的深入說明，請參閱 **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**。

```
.
├── README.md
├── apps/
│   ├── dashboard_api/
│   ├── main_dashboard/
│   ├── quant/
│   └── transcriber/
├── config/
├── core_utils/
├── docs/
│   └── ARCHITECTURE.md
├── logs/
├── run/
├── scripts/
│   ├── launch.py
│   ├── smart_e2e_test.py
│   └── ... (其他工具)
└── tests/
```
