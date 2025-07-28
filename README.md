# 🚀 鳳凰之心專案 (Phoenix Heart Project)

本專案旨在提供一套統一、簡潔且高效的微服務架構，使其能夠在本地開發環境（如 Ubuntu）和雲端演示環境（Google Colab）中無縫運行，並完整重現其精美的視覺化儀表板體驗。

## ✨ 核心特性

- **單一入口**: 所有操作皆由 `scripts/launch.py` 智慧化處理，無需關心環境差異。
- **架構清晰**: 原始碼、腳本、依賴與工具嚴格分離，易於理解和維護。
- **無縫環境切換**: 在本地開發和 Colab 演示之間提供完全一致的指令與體驗。
- **即時視覺化**: 透過 `GoTTY` 技術，將終端儀表板完美呈現於網頁，在 Colab 中可直接嵌入顯示。

## 📂 新專案結構

```
/
│
├── 📜 README.md           # 您正在閱讀的說明文件
│
├── 🚀 scripts/             # 【統一操作中心】
│   ├── launch.py           # ✨ 唯一的「智慧啟動器」，負責所有啟動任務
│   ├── phoenix_dashboard.py# ✨ 儀表板的原始碼
│   └── run_tests.sh        # ✨ 唯一的「整合測試器」
│
├── 📦 src/                 # 【核心原始碼】
│   ├── 📈 quant/           # Quant 服務 (包含其 tests/)
│   └── 🎤 transcriber/     # Transcriber 服務 (包含其 tests/)
│
├── 📋 requirements/       # 【集中依賴管理】
│   ├── base.txt
│   ├── quant.txt
│   ├── transcriber.txt
│   └── test.txt            # 測試專用的依賴
│
└── 🛠️ tools/               # 【內建輔助工具】
    └── gotty               # 將終端轉換為 Web 服務的利器
```

---

## ☁️ 在 Google Colab 中使用 (推薦)

Colab 提供了最簡單、最流暢的「啟動即看見」體驗。

**步驟 1: 準備專案**

在您的 Colab 筆記本的第一個儲存格中，使用 `git clone` 下載本專案。

```python
!git clone <您的專案 Git 倉庫網址>
%cd <專案目錄名稱>
```

**步驟 2: 一鍵啟動儀表板**

在第二個儲存格中，執行以下單一指令：

```python
!python scripts/launch.py --dashboard
```

執行完畢後，**「鳳凰之心指揮中心」儀表板將會自動出現在輸出格中**。您無需點擊任何連結，即可開始在這個熟悉的視覺化介面中進行所有操作。

---

## 💻 在本地環境開發與測試

智慧啟動器同樣簡化了本地的開發流程。

### 啟動微服務

這將在本地建立一個獨立的 Python 虛擬環境，安裝所有依賴，並在背景啟動 `quant` 和 `transcriber` 兩個微服務。

```bash
python3 scripts/launch.py
```

- **Quant 服務**: `http://localhost:8001`
- **Transcriber 服務**: `http://localhost:8002`
- 按 `Ctrl+C` 可優雅地關閉所有服務。

### 啟動本地儀表板

如果您想在本地使用儀表板，請執行：

```bash
python3 scripts/launch.py --dashboard
```

腳本將會提供一個本地網址 (預設為 `http://localhost:8080`)，請在瀏覽器中開啟它。

### 執行完整測試

我們提供了一個統一的測試腳本，它會自動處理環境準備、服務啟動、執行測試和事後清理。

```bash
bash scripts/run_tests.sh
```

此腳本會自動執行 `src/` 和 `tests/` 目錄下的所有測試，並在結束後妥善關閉所有因測試而啟動的服務。

---
感謝您使用「鳳凰之心」新架構！
