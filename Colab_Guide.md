# Colab 使用者指南：鳳凰之心作戰平台

## 簡介

歡迎使用「鳳凰之心」作戰平台！本平台專為在 Google Colab 環境中穩定、可靠地運行 Web 服務而設計。透過我們提供的 Colab 筆記本，您可以透過一個簡單的表單介面來設定並一鍵啟動您的服務。

平台會自動處理：

*   使用 `uv` 進行高速依賴安裝。
*   啟動後端 FastAPI 服務。
*   使用 Google Colab 的內建代理功能，生成一個**安全、私有**的應用程式連結。

## Colab 啟動介面

將下方的程式碼儲存格複製到您的 Colab 筆記本中。執行後，您會看到一個可互動的表單。

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

### 啟動儲存格程式碼 (v15.0)

<details>
<summary>點此展開/收合 🚀 啟動鳳凰之心整合式指揮中心 的程式碼</summary>

```python
#@title 💎 鳳凰之心整合式指揮中心 v15.0 (精簡版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **1. 顯示偏好設定**
#@markdown > **在啟動前，設定您的戰情室顯示偏好。**
#@markdown ---
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
#@markdown > **設定上半部「近期事件摘要」最多顯示的日誌行數。**
LOG_DISPLAY_LINES = 100 #@param {type:"integer"}
#@markdown **狀態刷新頻率 (秒) (STATUS_REFRESH_INTERVAL)**
#@markdown > **設定下半部「即時狀態指示燈」的刷新間隔，可為小數 (例如 0.5)。**
STATUS_REFRESH_INTERVAL = 0.5 #@param {type:"number"}

#@markdown ---
#@markdown ### **2. 專案路徑與伺服器設定**
#@markdown > **請指定要執行後端程式碼的資料夾名稱。**
#@markdown ---
#@markdown **指定專案資料夾名稱 (TARGET_FOLDER_NAME)**
#@markdown > **請輸入包含您後端程式碼 (例如 `main.py`, `colab_run.py`) 的資料夾名稱。例如：`WEB`。**
TARGET_FOLDER_NAME = "WEB" #@param {type:"string"}
#@markdown **日誌歸檔資料夾 (ARCHIVE_FOLDER_NAME)**
#@markdown > **最終的 .txt 日誌報告將儲存於此獨立的中文資料夾。**
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **後端服務埠號 (FASTAPI_PORT)**
#@markdown > **後端 FastAPI 應用程式監聽的埠號。**
FASTAPI_PORT = 8000 #@param {type:"integer"}
#@markdown ---
#@markdown > **準備就緒後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
#                      🚀 核心啟動器 (請勿修改) 🚀
# ==============================================================================
import os
import sys
from pathlib import Path

# --- 步驟 1: 組裝設定 ---
config = {
    "log_display_lines": LOG_DISPLAY_LINES,
    "status_refresh_interval": STATUS_REFRESH_INTERVAL,
    "archive_folder_name": ARCHIVE_FOLDER_NAME,
    "fastapi_port": FASTAPI_PORT,
}

# --- 步驟 2: 切換路徑並驗證 ---
project_path = Path(f"/content/{TARGET_FOLDER_NAME}")
if not project_path.is_dir():
    print(f"❌ 致命錯誤：找不到專案資料夾 '{project_path}'。")
    print("   請確認您已將專案上傳或 clone 到正確的位置，並且 TARGET_FOLDER_NAME 設定正確。")
else:
    os.chdir(project_path)
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))

    # --- 步驟 3: 呼叫後端橋接器 ---
    try:
        # 從專案中導入真正的執行器
        from colab_run import main as run_phoenix_engine

        # 執行主流程，傳入設定
        run_phoenix_engine(config)

    except ImportError:
        print(f"❌ 致命錯誤：無法導入 `colab_run` 模組。")
        print(f"   請檢查檔案 `colab_run.py` 是否存在於 '{project_path}' 中且無語法錯誤。")
    except Exception as e:
        import traceback
        print(f"💥 執行期間發生未預期的嚴重錯誤: {e}")
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
