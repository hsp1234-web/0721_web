# Colab 使用者指南：鳳凰之心作戰平台

## 簡介

歡迎使用「鳳凰之心」作戰平台！本平台專為在 Google Colab 環境中穩定、可靠地運行 Web 服務而設計。您無需關心複雜的環境設定和進程管理，只需將您的應用程式碼放入專案中，並使用下方的儲存格範本，即可一鍵啟動您的服務。

平台會自動處理：

*   依賴安裝
*   日誌監控
*   後端服務啟動
*   健康檢查
*   生成公開訪問連結

## Colab 儲存格範本

下方的儲存格是啟動平台的唯一入口。請點擊右上角的「複製」按鈕，然後將其貼到您的 Colab 筆記本中執行。

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
        import colab_run

        # 將 Colab 表單中由使用者設定的值，傳遞給主程式的全域變數
        colab_run.LOG_DISPLAY_LINES = LOG_DISPLAY_LINES
        colab_run.STATUS_REFRESH_INTERVAL = STATUS_REFRESH_INTERVAL
        colab_run.FASTAPI_PORT = FASTAPI_PORT
        colab_run.PROJECT_FOLDER_NAME = PROJECT_FOLDER_NAME

        # 打印啟動前的最終確認資訊
        print(f"\n✅ 成功導入版本: {getattr(colab_run, 'APP_VERSION', 'N/A')}。準備執行主流程...")
        print(f"   - 日誌顯示行數: {LOG_DISPLAY_LINES}")
        print(f"   - 狀態刷新頻率: {STATUS_REFRESH_INTERVAL} 秒")
        print(f"   - 後端服務埠號: {FASTAPI_PORT}")
        print("-" * 50)

        # 執行主作戰流程
        colab_run.main()

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

## 如何使用

1.  **準備專案**:
    *   在您的 Google Drive 中建立一個資料夾，例如 `Colab Notebooks`。
    *   將您的整個「鳳凰之心」專案（包含 `integrated_platform` 資料夾、`run.sh` 等）上傳到該資料夾下的一個子目錄，例如 `WEB`。
    *   結構應如下：`/content/drive/MyDrive/Colab Notebooks/WEB/`。

2.  **掛載 Google Drive**:
    *   在您的 Colab 筆記本中，執行以下程式碼來掛載您的 Google Drive：
        ```python
        from google.colab import drive
        drive.mount('/content/drive')
        ```

3.  **設定路徑**:
    *   在「🚀 啟動鳳凰之心作戰平台」儲存格中，將 `PROJECT_FOLDER_NAME` 的值修改為您在 Google Drive 中的完整路徑，例如：`drive/MyDrive/Colab Notebooks/WEB`。

4.  **執行**:
    *   執行該儲存格。平台將開始安裝依賴、啟動服務，並顯示一個包含日誌和公開連結的儀表板。
