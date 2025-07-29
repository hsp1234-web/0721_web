# 🚀 鳳凰之心 (Phoenix Heart) 專案 v9.2 - 智慧型系統 🚀

歡迎來到鳳凰之心，一個從單體架構中浴火重生的現代化微服務專案。本專案現已進化至 v9.2，搭載了完整的**智慧型資源管理與部署系統**。

它不僅是一個展示微服務化的範例，更是一個具備高度穩定性、資源感知與自動化能力的專業開發框架。

---

## 一、 核心理念與工具 (Core Philosophy & Tools)

我們的架構基於以下四大核心理念：

- **微服務架構 (Microservices)**: 每個 App (`quant`, `transcriber`) 都是一個獨立、可自行運行的 FastAPI 服務。
- **完全隔離 (Total Isolation)**: 每個 App 擁有自己獨立的虛擬環境，由主啟動腳本自動管理，彼此絕不干擾。
- **聲明式環境 (Declarative Environments)**: 每個 App 的依賴由其自己的 `requirements.txt` 精確聲明。
- **智慧型資源管理 (Intelligent Resource Management)**: 在安裝**每一個**套件前，系統都會即時檢查記憶體與磁碟資源，確保不會因資源耗盡而中斷，並將所有操作記錄在案。

### 核心工具鏈:

- **`phoenix_starter.py` (推薦)**: 專案的**視覺化啟動器**。一鍵完成資源檢查、智慧型安裝、執行測試，並提供精美的儀表板全程監控。
- **`launch.py`**: 專案的**主啟動腳本 (無介面)**，適合在伺服器或自動化腳本中執行。
- **`core_utils/safe_installer.py`**: 專案的**安全安裝模組**。它取代了傳統的 `pip install -r`，逐一套件進行安裝，並在每一步都進行資源檢查。
- **`core_utils/resource_monitor.py`**: 專案的**資源監控模組**，提供檢查記憶體與磁碟的底層能力。
- **`config/resource_settings.yml`**: **全域設定中心**，所有資源閾值（記憶體、磁碟）都在此統一定義，方便您根據不同主機環境進行調整。
- **`logs/`**: **日誌中心**，所有安裝與啟動過程的詳細日誌都儲存在此，方便追蹤與除錯。
- **uv**: 我們唯一的環境管理與安裝工具，由安全安裝模組在底層呼叫。
- **FastAPI**: 我們所有微服務使用的現代、高效能 Web 框架。

---

## 二、 如何開始 (Getting Started)

### 2.1. 視覺化啟動與測試 (推薦)

在任何支持 Python 的環境中，只需一個命令即可啟動鳳凰之心視覺化啟動器：

```bash
python phoenix_starter.py
```

這個命令會自動為您完成**所有事情**，並在一個精美的儀表板上顯示所有進度，最終畫面如下：

```text
┌─ 🚀 鳳凰之心視覺化啟動器 v9.2 ───────────────────────────────────────────────┐
│                                                                              │
├─ 🌐 系統狀態 (System Status) ────────────────────────────────────────────────┤
│ 🟢 運行中   核心: 25.6%   RAM: 0.3/8.3 GB (6.8%)   DISK: 1.0/10.5 GB (10.2%)  │
│                                                                              │
├─ 📦 應用程式狀態 (Application Status) ───────────────────────────────────────┤
│ 📈 Quant App         [🟢 測試通過]         🎤 Transcriber App   [🟢 測試通過]         │
│                                                                              │
├─ 📜 即時日誌 (Live Logs) ────────────────────────────────────────────────────┤
│ [04:59:53] [INFO] ============================== 4 passed in 2.62s =============================== │
│ [04:59:53] [INFO] --- 開始為 App 'transcriber' 進行安全安裝 ---             │
│ [04:59:53] [INFO] --- [4/4] 準備安裝: pydantic ---                          │
│ [04:59:53] [INFO] 資源充足。開始安裝 'pydantic'...                         │
│ [04:59:55] [INFO] ========================= 4 passed, 1 skipped in 0.63s ========================= │
│                                                                              │
├─ ✨ 當前任務 (Current Task) ─────────────────────────────────────────────────┤
│ [空閒]                                                                       │
│                                                                              │
└──────────────────────────────────────────────────────────────────────────────┘
```
**核心流程：**
1.  檢查並安裝 `uv`, `psutil`, `pyyaml` 等核心工具。
2.  讀取 `config/resource_settings.yml` 中的資源閾值。
3.  為 `apps/` 下的每一個 App 建立獨立的虛擬環境。
4.  呼叫**安全安裝模組**，在監控下逐一安全地為每個 App 安裝依賴。
5.  在儀表板上即時顯示詳細的安裝日誌。
6.  執行所有測試 (`tests/`)。
7.  所有任務完成後，畫面將會保留，直到您按下 Enter 鍵。

### 2.2. 無介面啟動 (適用於伺服器)

若您在沒有 TUI 的環境中，可以使用 `launch.py`：

```bash
python launch.py
```

它會執行與視覺化啟動器完全相同的安全流程，只是將所有日誌直接輸出到您的控制台。

### 2.3. 在 Google Colab 中啟動

我們提供了完整的 Google Colab 整合方案，讓您可以一鍵在 Colab 環境中部署、測試和運行整個專案。

詳細的操作指南，請參考 [**Colab 使用指南**](docs/Colab_Guide.md)。

---

## 三、 檔案結構總覽 (v9.2 - 完整版)

```
/PHOENIX_HEART_PROJECT/
│
├── 🚀 phoenix_starter.py          # 【推薦】視覺化啟動器，整合所有功能。
├── 🚀 launch.py                   # 【無介面】主啟動腳本，適合伺服器環境。
├── 📜 smart_e2e_test.sh           # 智能測試腳本，由安全安裝模組驅動。
│
├── 📦 apps/                        # 【所有獨立微服務的家】
│   ├── 📈 quant/                   #  - 量化金融 App
│   │   ├── api/                  #    - API 接口層
│   │   │   └── v1/               #      - API 版本 v1
│   │   │       └── routes.py     #        - FastAPI 路由定義
│   │   ├── logic/                #    - 核心業務邏輯
│   │   │   ├── analysis.py       #      - 分析與策略邏輯
│   │   │   ├── data_sourcing.py  #      - 數據源邏輯
│   │   │   ├── database.py       #      - 資料庫邏輯
│   │   │   └── factor_engineering.py #  - 因子工程邏輯
│   │   ├── main.py               #    - App 的 FastAPI 入口
│   │   └── requirements.txt      #    - Python 核心依賴
│   │
│   └── 🎤 transcriber/             #  - 語音轉寫 App
│       ├── main.py               #    - App 的 FastAPI 入口
│       ├── logic.py              #    - 核心業務邏輯
│       ├── requirements.txt      #    - Python 核心依賴
│       └── requirements.large.txt#    - (可選) 大型 AI 模型依賴
│
├── 🛠️ core_utils/                 # 【核心工具模組】
│   ├── __init__.py               #  - 將此目錄標記為 Python 套件。
│   ├── resource_monitor.py       #  - 資源監控模組：提供檢查系統資源的函式。
│   └── safe_installer.py         #  - 安全安裝模組：逐一套件、帶資源檢查地執行安裝。
│
├── ⚙️ config/                     # 【全域設定中心】
│   └── resource_settings.yml     #  - 在此定義記憶體/磁碟閾值等監控參數。
│
├── 📝 logs/                        # 【日誌中心】
│   └── .gitkeep                  #  - 所有安裝與啟動日誌的存放處 (log檔會被自動忽略)。
│
├── 🧪 tests/                       # 【品質保證中心】
│   ├── 📈 quant/                   #  - 量化金融 App 的測試
│   │   └── test_api.py           #    - API 層級的整合測試
│   └── 🎤 transcriber/             #  - 語音轉寫 App 的測試
│       └── test_api.py           #    - API 層級的整合測試 (包含模擬與 E2E)
│
├── ⚙️ proxy/                        # 【逆向代理配置】
│   └── proxy_config.json         #  - 路由規則設定檔。
│
├── 📚 docs/                         # 【專案文件】
│   ├── ARCHITECTURE.md           #  - 深入的架構設計藍圖
│   ├── Colab_Guide.md            #  - Google Colab 運行指南
│   ├── MISSION_DEBRIEFING.md     #  - 專案任務報告
│   └── TEST.md                   #  - 測試策略說明
│
├── 🗄️ ALL_DATE/                   # 【舊專案封存 (參考用)】
│
└── 📄 .gitignore                  # Git 忽略檔案設定。
```
