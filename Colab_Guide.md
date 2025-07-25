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

### 啟動儲存格程式碼 (v4.0)

<details>
<summary>點此展開/收合 🚀 啟動鳳凰之心引擎 的程式碼</summary>

```python
#@title 🚀 啟動鳳凰之心引擎 (v4.0)
#@markdown ---
#@markdown ### **1. 專案與伺服器設定**
#@markdown > **`PROJECT_FOLDER_NAME` 是您在 `/content/` 下的專案資料夾名稱。**
PROJECT_FOLDER_NAME = "WEB" #@param {type:"string"}
#@markdown > **`FASTAPI_PORT` 是您的後端服務運行的埠號。**
FASTAPI_PORT = 8000 #@param {type:"integer"}

# ==============================================================================
#                      ⚠️ 請勿修改下方的引導程式碼 ⚠️
# ==============================================================================
import os
import sys
import time
from pathlib import Path
import traceback

# --- 步驟 1: 設定工作目錄 ---
project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")
if not project_path.is_dir():
    print(f"❌ 致命錯誤：找不到專案資料夾 '{project_path}'。")
    print("   請確認您已將專案上傳或 clone 到正確的位置，並且 PROJECT_FOLDER_NAME 設定正確。")
else:
    os.chdir(project_path)
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))
    print(f"✅ 工作目錄已成功切換至: {os.getcwd()}")

    # --- 步驟 2: 安裝依賴 ---
    # 使用 uv 來加速安裝
    print("\n--- 正在安裝依賴... ---")
    os.system("pip install uv")
    os.system("uv pip install -r requirements.txt")
    print("✅ 依賴安裝完畢。")

    # --- 步驟 3: 啟動後端引擎並嵌入駕駛艙 ---
    try:
        from colab_run import start_backend, stop_backend
        from google.colab import output

        print("\n--- 正在啟動後端引擎... ---")
        # 在背景啟動 FastAPI 伺服器
        start_backend(port=FASTAPI_PORT)

        print("\n--- 引擎預熱中，請稍候 (15秒)... ---")
        time.sleep(15)

        print("\n--- 正在嵌入前端駕駛艙... ---")
        # 將由後端託管的前端介面嵌入到 Colab 輸出中
        output.serve_kernel_port_as_iframe(
            port=FASTAPI_PORT,
            height=600  # 您可以調整內嵌視窗的高度
        )
        print("✅ 駕駛艙已成功嵌入。所有遙測數據將顯示在下方視窗中。")
        print("   如果視窗未顯示，請檢查上方的日誌輸出是否有錯誤。")

        # 保持主執行緒運行，以便 atexit 可以正常工作
        print("\n--- 引擎正在運行。關閉此 Colab 執行環境將自動終止後端服務。 ---")
        while True:
            time.sleep(3600)

    except ImportError as e:
        print(f"❌ 致命錯誤：無法導入 `colab_run` 模組。")
        print(f"   請檢查檔案 `colab_run.py` 是否存在且無語法錯誤。")
        print(f"   詳細錯誤: {e}")
    except Exception as e:
        print(f"💥 執行期間發生未預期的錯誤: {e}")
        traceback.print_exc()
    finally:
        # 確保在任何情況下退出時都能嘗試關閉後端
        print("\n--- 正在執行清理程序... ---")
        stop_backend()

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
