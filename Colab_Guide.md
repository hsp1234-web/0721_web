# Colab 使用者指南：鳳凰之心作戰平台

## 簡介

歡迎使用「鳳凰之心」作戰平台！本平台專為在 Google Colab 環境中穩定、可靠地運行 Web 服務而設計。透過我們提供的 Colab 筆記本，您可以透過一個簡單的表單介面來設定並一鍵啟動您的服務。

平台會自動處理：

*   使用 `uv` 進行高速依賴安裝。
*   啟動後端 FastAPI 服務。
*   使用 Google Colab 的內建代理功能，生成一個**安全、私有**的應用程式連結。

## Colab 啟動介面

將下方的程式碼儲存格複製到您的 Colab 筆記本中。執行後，您會看到一個可互動的表單。

![Colab 表單示意圖](https://i.imgur.com/your-image-url.png)  <!-- 我會在這裡放一個示意圖的佔位符 -->

### 如何設定

在執行儲存格之前，請根據您的需求設定以下參數：

#### 1. 顯示偏好設定
> **在啟動前，設定您的戰情室顯示偏好。**

*   `LOG_DISPLAY_LINES`: (即將實裝) 設定日誌儀表板中顯示的日誌行數。
*   `STATUS_REFRESH_INTERVAL`: (即將實裝) 設定狀態面板的刷新頻率（秒）。

#### 2. 專案與伺服器設定
> **`PROJECT_FOLDER_NAME` 是您在 `/content/` 下的專案資料夾名稱。**

*   `PROJECT_FOLDER_NAME`: 這是您存放整個專案的資料夾名稱。
    *   如果您是透過 `git clone https://github.com/user/repo.git WEB` 克隆的，那這裡就填 `WEB`。
    *   如果您將專案放在 Google Drive 的 `MyDrive/MyProject` 中，並已掛載 Drive，那這裡就填 `drive/MyDrive/MyProject`。
*   `FASTAPI_PORT`: 您的後端 FastAPI 應用程式將在此埠號上運行。`colab_run.py` 會將這個埠號暴露給 Colab 的代理。預設值為 `8000`。

### 啟動儲存格程式碼

<details>
<summary>點此展開/收合 🚀 啟動鳳凰之心作戰平台 的程式碼</summary>

```python
#@title 🚀 啟動鳳凰之心作戰平台 (v2.1.0)
#@markdown ---
#@markdown ### **1. 顯示偏好設定**
#@markdown > **在啟動前，設定您的戰情室顯示偏好。**
LOG_DISPLAY_LINES = 100 #@param {type:"integer"}
STATUS_REFRESH_INTERVAL = 1.0 #@param {type:"number"}

#@markdown ---
#@markdown ### **2. 專案與伺服器設定**
#@markdown > **`PROJECT_FOLDER_NAME` 是您在 `/content/` 下的專案資料夾名稱。**
PROJECT_FOLDER_NAME = "WEB" #@param {type:"string"}
#@markdown > **`FASTAPI_PORT` 是您的後端服務運行的埠號。**
FASTAPI_PORT = 8000 #@param {type:"integer"}

# ==============================================================================
#                      ⚠️ 請勿修改下方的引導程式碼 ⚠️
# ==============================================================================
import os
import sys
from pathlib import Path
import traceback

# --- 步驟 1: 設定工作目錄 ---
# 確保我們的執行環境在專案的根目錄下
project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")
if not project_path.is_dir():
    print(f"❌ 致命錯誤：找不到專案資料夾 '{project_path}'。")
    print("   請確認您已將專案上傳或 clone 到正確的位置，並且 PROJECT_FOLDER_NAME 設定正確。")
else:
    os.chdir(project_path)
    # 將專案路徑添加到系統路徑中，以便 Python 可以找到我們的模組
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))
    print(f"✅ 工作目錄已成功切換至: {os.getcwd()}")

    # --- 步驟 2: 執行主引導程序 ---
    try:
        # 從專案中導入主引導模組
        # 我們在這裡重新命名導入，以避免與內建的 'run' 衝突
        import colab_run as PlatformLauncher

        # 將 Colab 表單中由使用者設定的值，傳遞給主程式的全域變數
        # 注意：這需要在 colab_run.py 中預先定義這些變數
        PlatformLauncher.PORT = FASTAPI_PORT
        # PlatformLauncher.LOG_DISPLAY_LINES = LOG_DISPLAY_LINES (待實作)
        # PlatformLauncher.STATUS_REFRESH_INTERVAL = STATUS_REFRESH_INTERVAL (待實作)

        # 打印啟動前的最終確認資訊
        print(f"\n✅ 成功導入啟動器。準備執行主流程...")
        print(f"   - 專案資料夾: {PROJECT_FOLDER_NAME}")
        print(f"   - 後端服務埠號: {FASTAPI_PORT}")
        print("-" * 50)

        # 執行主作戰流程
        PlatformLauncher.main()

    except ImportError as e:
        print(f"❌ 致命錯誤：無法導入主引導程序 `colab_run`。")
        print(f"   請檢查檔案 `colab_run.py` 是否存在且無語法錯誤。")
        print(f"   詳細錯誤: {e}")
    except Exception as e:
        print(f"💥 執行期間發生未預期的錯誤: {e}")
        # 打印詳細的錯誤追蹤資訊，以便除錯
        traceback.print_exc()

```
</details>

## 執行與訪問

1.  **設定參數**：根據您的專案位置和偏好，填寫表單中的四個欄位。
2.  **執行儲存格**：點擊儲存格左側的「播放」按鈕。
3.  **查看輸出**：程式將開始執行，並依序打印出：
    *   工作目錄切換確認。
    *   啟動參數確認。
    *   依賴安裝日誌。
    *   FastAPI 伺服器啟動日誌。
4.  **訪問應用**：當一切就緒後，Colab 會在輸出儲存格的下方生成一個內嵌的應用程式視窗，並同時提供一個可在新分頁開啟的連結。

    > 👇 您的應用程式正在下方內嵌視窗中運行。
    >
    > 或者，點此在新分頁中全螢幕開啟

您可以直接在內嵌視窗中操作，或點擊連結以獲得全螢幕體驗。
