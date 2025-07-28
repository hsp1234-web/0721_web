# 🚀 鳳凰之心 (Phoenix Heart) 專案 🚀

歡迎來到鳳凰之心，一個從單體架構中浴火重生的現代化微服務專案。

本專案旨在展示如何將一個傳統、混合的 Python 應用，重構為一個清晰、可擴展、易於維護的微服務系統。它由兩個核心微服務組成：一個用於**量化金融分析 (Quant)**，另一個用於**語音轉寫 (Transcriber)**。

---

## 一、 核心理念與工具 (Core Philosophy & Tools)

我們的架構基於以下三大核心理念，並由一套精簡的工具鏈來實現：

- **微服務架構 (Microservices)**: 每個 App (`quant`, `transcriber`) 都是一個獨立、可自行運行的 FastAPI 服務。
- **完全隔離 (Total Isolation)**: 每個 App 擁有自己獨立的虛擬環境 (`.venv`)，由唯一的總開關 `launch.py` 自動管理，彼此絕不干擾。
- **聲明式環境 (Declarative Environments)**: 每個 App 的依賴由其自己的 `requirements.txt` 精確聲明，保證了環境的極速建立與可重複性。

### 核心工具鏈:

- **uv**: 我們唯一的環境管理與安裝工具。負責以極致速度建立虛擬環境 (`.venv`) 和同步 Python 套件。
- **`launch.py`**: 專案的「總開關」，負責協調所有工具，一鍵啟動整個系統。
- **FastAPI**: 我們所有微服務使用的現代、高效能 Web 框架。
- **`smart_e2e_test.sh`**: 專案的「品質指揮官」，一個智能化的端到端測試腳本，支持模擬與真實兩種測試模式。

---

## 二、 如何開始 (Getting Started)

### 2.1. 啟動整個系統

在任何支持 Python 的環境中（本地、Colab、伺服器），只需一個命令即可啟動所有服務：

```bash
python launch.py
```

這個命令會自動為您完成所有事情：
1.  檢查並安裝 `uv`。
2.  為 `apps/` 目錄下的每一個 App 建立獨立的 `.venv` 虛擬環境。
3.  在每個虛擬環境中，光速安裝其 `requirements.txt` 中聲明的依賴。
4.  在背景啟動所有 App 的 FastAPI 伺服器。
5.  啟動一個逆向代理，監聽 `http://localhost:8000`。

**啟動成功後，您可以這樣訪問服務：**
- **量化金融 App**: `http://localhost:8000/quant/v1/...`
- **語音轉寫 App**: `http://localhost:8000/transcriber/...`

### 2.2. 運行測試

我們提供一個強大的整合測試腳本，支持兩種模式。

#### 模擬模式 (預設，快速)

這是最常用的模式，它會測試所有的 API 介面和業務邏輯，但會**跳過**安裝大型依賴（如 `torch`）和執行耗時的 AI 模型計算。它適用於日常開發和快速驗證。

```bash
bash smart_e2e_test.sh
```

#### 真實模式 (完整，較慢)

此模式會安裝所有依賴（包括 `requirements.large.txt` 中的大型依賴），並執行完整的端到端測試。請確保您有足夠的磁碟空間和網路連線。

```bash
TEST_MODE=real bash smart_e2e_test.sh
```

---

## 三、 檔案結構總覽

```
/PHOENIX_HEART_PROJECT/
│
├── 🚀 launch.py                 # 唯一的「總開關」，一鍵啟動所有服務。
│
├── 📦 apps/                      # 【所有獨立微服務的家】
│   │
│   ├── 📈 quant/                 # 【量化金融 App】
│   │   ├── 🛰️ main.py             # FastAPI 入口
│   │   ├── 🧠 logic/             # 核心業務邏輯
│   │   ├── 🕸️ api/                # API 接口層
│   │   ├── 📜 requirements.txt     # 核心依賴
│   │   └── 🧪 tests/             # 獨立的測試
│   │
│   └── 🎤 transcriber/           # 【語音轉寫 App】
│       ├── 🛰️ main.py             # FastAPI 入口
│       ├── 🧠 logic.py           # 核心業務邏輯
│       ├── 📜 requirements.txt     # 核心依賴
│       ├── 📜 requirements.large.txt # (可選) 大型依賴
│       └── 🧪 tests/             # 獨立的測試
│
├── ⚙️ proxy/                      # 【逆向代理配置】
│   └── proxy_config.json       # 路由規則設定檔
│
├── 📜 smart_e2e_test.sh         # 智能測試指揮官腳本
│
├── 📚 docs/                       # 【專案文件】
│   └── ARCHITECTURE.md         # 最終的架構設計總藍圖
│
└── 🗄️ ALL_DATE/                 # 【封存參考資料】
```
