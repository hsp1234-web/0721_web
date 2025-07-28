# 🚀 鳳凰之心專案 (Phoenix Heart Project)

歡迎來到鳳凰之心專案！本專案已經過重構，採用了現代化的微服務架構，旨在提供清晰、可維護且易於部署的開發體驗。

## ✨ 核心理念

- **統一入口**: 所有操作都從 `scripts/launch.py` 開始。
- **職責分離**: 原始碼、腳本、依賴和工具各歸其位。
- **環境無關**: 在本地 (Ubuntu/macOS) 和雲端 (Colab) 提供一致的體驗。
- **視覺化管理**: 提供一個精美的終端儀表板來監控和互動。

## 📂 檔案結構概覽

```
/
│
├── 📜 README.md           # 就是你正在看的這個檔案
│
├── 📦 src/                 # 【核心原始碼】所有微服務的家
│   ├── 📈 quant/           # Quant App 的 Python 套件
│   └── 🎤 transcriber/     # Transcriber App 的 Python 套件
│
├── 🚀 scripts/             # 【統一操作中心】所有使用者指令的入口
│   ├── launch.py           # ✨ 唯一的「智慧啟動器」
│   ├── phoenix_dashboard.py# ✨ 終端儀表板的程式碼
│   └── run_tests.sh        # ✨ 統一的整合測試器
│
├── 📋 requirements/       # 【集中依賴管理】
│   ├── base.txt            # 所有服務共享的基礎依賴
│   ├── quant.txt           # Quant App 的特定依賴
│   └── transcriber.txt     # Transcriber App 的特定依賴
│
├── 🛠️ tools/               # 【內建工具庫】
│   └── gotty               # 用於將儀表板 Web 化的工具
│
├── ⚙️ proxy/               # (不變) 逆向代理設定
│
└── 🗄️ ALL_DATE/           # (不變) 封存的參考資料
```

## 🚀 快速上手

所有操作都透過 `scripts/launch.py` 進行。它會自動為您處理虛擬環境和依賴安裝。

### 1. 啟動後端服務

這將在背景啟動 `quant` 和 `transcriber` 兩個微服務。

```bash
python scripts/launch.py
```

服務將分別運行在 `http://localhost:8001` (quant) 和 `http://localhost:8002` (transcriber)。按 `Ctrl+C` 可以優雅地關閉所有服務。

### 2. 啟動互動式儀表板

這將啟動一個基於網頁的終端儀表板，您可以在其中即時監控服務狀態並執行測試。

```bash
python scripts/launch.py --dashboard
```

啟動後，請在瀏覽器中開啟 `http://localhost:8080` 來查看儀表板。

### 3. 執行整合測試

如果您只想運行測試套件，請使用 `run_tests.sh` 腳本。

```bash
bash scripts/run_tests.sh
```

此腳本會：
1.  呼叫 `launch.py --prepare-only` 來自動安裝所有必要的依賴。
2.  使用 `pytest` 執行 `src/` 目錄下的所有測試。

---
感謝您使用新架構！
