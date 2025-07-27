# Colab 使用指南 v2.0：鳳凰之心指揮中心

## 簡介

歡迎使用新一代的「鳳凰之心指揮中心」！本平台經過全新設計，旨在 Google Colab 環境中提供最穩定、可靠且使用者友善的 Web 服務啟動體驗。

新版啟動器 (`launcher`) 會自動處理：
*   讀取您的設定。
*   提供一個美觀的即時儀表板，顯示系統狀態和日誌。
*   在安裝大型依賴前預先檢查磁碟空間，避免崩潰。
*   在背景安全地啟動您的後端 FastAPI 服務。
*   為您的應用程式生成一個安全、私有的 Colab 訪問連結。

## 如何啟動

您只需要在 Colab 中上傳並執行 `launcher.ipynb` 筆記本即可。

### 啟動介面

`launcher.ipynb` 提供了一個簡單的表單，讓您設定幾個關鍵參數：

*   `REPOSITORY_URL`: 您後端程式碼所在的 Git 倉庫地址。
*   `TARGET_BRANCH_OR_TAG`: 您想要部署的分支或標籤名稱。
*   `PROJECT_FOLDER_NAME`: 您的專案將被下載到 Colab 的哪個資料夾中。
*   `FORCE_REPO_REFRESH`: 是否在每次啟動時都強制刪除舊的程式碼並重新下載。

### 執行步驟

1.  **打開 `launcher.ipynb`**: 在 Colab 中打開此筆記本。
2.  **設定參數**：在第一個程式碼儲存格的表單中，填寫您的專案資訊。
3.  **執行儲存格**：點擊儲存格左側的「播放」按鈕。
4.  **監控儀表板**: 執行後，一個由 `rich` 函式庫驅動的儀表板將會出現。您可以從中看到詳細的啟動流程、系統資源使用情況和即時日誌。
5.  **訪問應用**：當後端服務完全上線後，儀表板的「系統狀態」區域會出現一個 `應用 URL`。點擊該連結，即可在新分頁中與您的應用程式互動。

### 範例 `launcher.ipynb` 儲存格

```python
#@title 🚀 啟動指揮中心 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "2.1.2" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

import os
from pathlib import Path
import toml

# --- 將使用者設定寫入設定檔 ---
# (此處為筆記本內部邏輯，自動處理設定檔生成)
# ...

# --- 執行啟動器 ---
!python /content/launcher/src/main.py
```

這份經過大幅簡化的指南旨在讓使用者能更快上手。所有複雜的邏輯都已被封裝在 `launcher` 模組中，使用者無需關心其內部細節。
