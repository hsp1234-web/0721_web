# Colab 使用者指南：鳳凰之心作戰平台

## 簡介

歡迎使用「鳳凰之心」作戰平台！本平台專為在 Google Colab 環境中穩定、可靠地運行 Web 服務而設計。透過我們提供的 Colab 筆記本，您可以一鍵啟動您的服務。

平台會自動處理：

*   使用 `uv` 進行高速依賴安裝。
*   啟動後端 FastAPI 服務。
*   **在 Colab 儲存格中直接渲染一個全功能的純文字儀表板，即時監控系統狀態。**

## Colab 啟動介面

將下方的程式碼儲存格複製到您的 Colab 筆記本中。執行後，您會看到一個互動式儀表板。

### 啟動儲存格程式碼

<details>
<summary>點此展開/收合 🚀 啟動鳳凰之心儀表板指揮中心 的程式碼</summary>

```python
# 1. 克隆專案
!git clone https://github.com/YOUR_USERNAME/YOUR_REPOSITORY.git
%cd YOUR_REPOSITORY

# 2. 執行設定腳本
!./setup.sh

# 3. 啟動儀表板
import run
run.display_dashboard()
```
</details>

## 執行與訪問

1.  **執行儲存格**：點擊儲存格左側的「播放」按鈕。
2.  **查看儀表板**：程式將開始執行，儲存格的輸出會被一個動態的、持續更新的**純文字儀表板**所取代。您可以在此處即時監控：
    *   CPU 和 RAM 使用率。
    *   核心服務的運行狀態。
    *   最新的關鍵日誌。
3.  **訪問應用**：若要與應用程式互動，您需要另外啟動 `server_main.py`。
