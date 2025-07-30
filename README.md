# 🚀 鳳凰之心 (Phoenix Heart) 專案 v13 - 彈性啟動架構 🚀

歡迎來到鳳凰之心 v13。本專案已從一個智慧型系統，進化為一個具備**彈性啟動 (Resilient Startup)** 能力的現代化微服務編排框架。

新架構的核心是**分階段啟動**與**完全解耦的 JSON 日誌流**，旨在提供極致的穩定性、卓越的使用者體驗和前所未有的可觀測性。

---

## 一、 核心理念 (v13)

我們的架構基於以下四大核心理念：

- **分階段啟動 (Staged Loading)**: 系統啟動分為兩個階段。**階段一**在幾秒內啟動核心 API 閘道，讓前端介面立刻可用。**階段二**在背景平行地、非同步地載入耗資源的業務服務 (`quant`, `transcriber`)。這確保了核心系統的即時回應和高容錯性。
- **微服務與完全隔離 (Microservices & Isolation)**: 每個業務服務都在自己獨立的虛擬環境中運行，由主啟動腳本自動管理。一個服務的失敗完全不影響其他服務。
- **JSON 結構化日誌 (JSON-Structured Logging)**: 後端不再產生用於「顯示」的儀表板。取而代之的是，所有服務（包括啟動器、業務邏輯、效能監控）都將其狀態以**純粹的 JSON 字串**格式輸出到標準輸出 (stdout)。
- **前端完全解耦 (Decoupled Frontend)**: 前端（無論是 Colab、Web App 或其他監控系統）的唯一任務就是讀取後端的 JSON 日誌流，並根據這些數據來渲染自己的介面。這實現了前後端的終極解耦。

---

## 二、 如何開始 (Getting Started)

本專案提供兩種主要的啟動方式，分別對應不同的使用場景。

### 2.1. 純後端模式 (Headless Backend Mode)

此模式適用於伺服器、Docker 或任何自動化環境。它沒有任何 UI，只會將 JSON 日誌串流輸出到主控台。

```bash
# 啟動所有後端服務
python run/backend_runner.py
```

您將會看到連續的 JSON 輸出，可用於日誌收集、分析或驅動您自己的前端。

### 2.2. Google Colab 視覺化模式

此模式專為在 Google Colab 中進行互動式開發和監控而設計。

請在 Colab 的儲存格中執行：
```python
!python run/colab_runner.py
```
`colab_runner.py` 會在底層呼叫 `backend_runner.py`，並即時解析其輸出的 JSON 日誌，最後用 `rich` 套件渲染出一個美觀、即時更新的儀表板。

---

## 三、 測試我們的架構

我們將所有測試整合到一個單一的、功能強大的測試腳本中。它不僅測試業務邏輯，更重要的是，它測試我們架構本身的健壯性。

```bash
# 執行所有整合測試
python -m pytest tests/test_all.py
```

此測試會驗證分階段啟動、服務失敗時的容錯能力、API 閘道功能以及日誌格式的正確性。

---

## 四、 新版檔案結構總覽 (v13)

```
/PHOENIX_HEART_PROJECT/
│
├── 📂 apps/                       # 所有微服務的家
│   ├── 📈 quant/                  # - 量化金融 App
│   ├── 🎤 transcriber/            # - 語音轉寫 App
│   └── 🌐 api_server/             # - 【核心】統一 API 閘道
│
├── 📂 run/                        # 啟動腳本
│   ├── 🚀 backend_runner.py       # - 【核心】純後端啟動編排器 (輸出 JSON)
│   └── 🏃 colab_runner.py        # - Colab 視覺化啟動器 (解析 JSON)
│
├── 📂 utils/                      # 核心工具
│   └── 🛡️ resource_monitor.py    # - 高頻資源監控腳本
│
├── 📂 config/                     # 全域設定
│   ├── ⚙️ services.json          # - 定義所有可啟動的業務服務
│   └── ...
│
├── 📂 tests/                      # 品質保證中心
│   └── 🧪 test_all.py              # - ✨【唯一】的整合測試腳本
│
├── 📂 archive/                    # 封存的歷史專案
│
├── 📂 logs/                       # 日誌 (可選，主要日誌流在 stdout)
│
└── 📄 .gitignore
```
---

## 五、 深入了解

想要更深入地了解我們的設計哲學、分階段啟動的具體實現以及 API 閘道的角色嗎？

請參閱我們的**權威性架構藍圖**: **`docs/ARCHITECTURE.md`**。
