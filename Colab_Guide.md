# Colab 使用者指南

歡迎使用鳳凰之心專案！本指南將引導您如何在 Google Colab 環境中輕鬆啟動和使用本專案。

## 簡介

本專案在 Colab 中提供了一個**整合式指揮中心**介面。您不再需要查看零散的日誌輸出，而是可以在一個整合的面板中，即時監控系統狀態、查看事件日誌，並直接與您的應用程式互動。

![架構圖](https_//i.imgur.com/example.png)  <-- 這裡可以放一張新UI的截圖

## 快速啟動

整個專案的啟動過程非常簡單，只需要在 Colab 中執行一個儲存格即可。

### 步驟 1: 準備您的環境

1.  **開啟 Google Colab**: [https://colab.research.google.com/](https://colab.research.google.com/)
2.  **連接到執行個體**: 點擊右上角的「連線」。
3.  **上傳或 Clone 專案**:
    *   **方式一 (建議)**: 在 Colab 儲存格中執行 `!git clone [您的專案 Git 倉庫 URL]`。
    *   **方式二**: 手動從左側的「檔案」面板上傳您的整個專案資料夾。

### 步驟 2: 執行整合式指揮中心

將下方所有的程式碼複製到一個新的 Colab 儲存格中，然後點擊左側的「執行」按鈕。

---

#### 💎 **鳳凰之心整合式指揮中心 v3.0**

```python
#@title 💎 鳳凰之心整合式指揮中心 v3.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **1. 顯示偏好設定**
#@markdown > **在啟動前，設定您的戰情室顯示偏好。**
#@markdown ---
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
#@markdown > **設定上半部「近期事件摘要」最多顯示的日誌行數。**
LOG_DISPLAY_LINES = 50 #@param {type:"integer"}
#@markdown **狀態刷新頻率 (秒) (STATUS_REFRESH_INTERVAL)**
#@markdown > **設定「即時狀態指示燈」的刷新間隔，可為小數 (例如 0.2)。**
STATUS_REFRESH_INTERVAL = 0.2 #@param {type:"number"}

#@markdown ---
#@markdown ### **2. 專案路徑與伺服器設定**
#@markdown > **請指定要執行後端程式碼的資料夾名稱。**
#@markdown ---
#@markdown **指定專案資料夾名稱 (TARGET_FOLDER_NAME)**
#@markdown > **請輸入包含您後端程式碼 (例如 `main.py`) 的資料夾名稱。例如：`WEB`。**
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
#                      ⚠️ 請勿修改下方的引導程式碼 ⚠️
# ==============================================================================
import os
import sys
from pathlib import Path
import traceback

# --- 步驟 1: 設定工作目錄與環境 ---
# 專案的根目錄是在 /content/ 下
# 但我們的腳本 (colab_run.py 等) 是在專案資料夾內
# 所以工作目錄應該是專案資料夾本身
project_path = Path.cwd()

# 檢查是否在 Colab 預期的 /content 目錄下
if project_path.parent.name != 'content':
    print(f"⚠️ 警告：目前工作目錄為 '{project_path}'，非預期的 '/content' 子目錄。")
    print(f"   如果您的專案不是位於 '/content' 下，請確保路徑設定正確。")

if not project_path.is_dir():
    print(f"❌ 致命錯誤：找不到專案資料夾 '{project_path}'。")
    print("   請確認您已將專案上傳或 clone 到正確的位置。")
else:
    # 將專案路徑加入 sys.path 以確保模組可以被正確導入
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))
    print(f"✅ 工作目錄已確認: {os.getcwd()}")

    # --- 步驟 2: 執行點火器 (Ignition) ---
    try:
        # 導入點火器模組
        import colab_run

        # 將此處 @param 表單的值，直接賦予給點火器模組中的全域變數
        colab_run.LOG_DISPLAY_LINES = LOG_DISPLAY_LINES
        colab_run.STATUS_REFRESH_INTERVAL = STATUS_REFRESH_INTERVAL
        colab_run.TARGET_FOLDER_NAME = TARGET_FOLDER_NAME
        colab_run.ARCHIVE_FOLDER_NAME = ARCHIVE_FOLDER_NAME
        colab_run.FASTAPI_PORT = FASTAPI_PORT

        print("✅ 參數已傳遞，準備點火...")
        print("-" * 50)

        # 執行點火器，它將呼叫主引擎並接管後續所有流程
        colab_run.main()

    except ImportError:
        print(f"❌ 致命錯誤：找不到點火器腳本 'colab_run.py'。")
        print(f"   請確認該檔案存在於 '{project_path}' 中且無語法錯誤。")
        traceback.print_exc()
    except Exception as e:
        print(f"💥 駕駛艙執行時發生未預期的錯誤: {e}")
        traceback.print_exc()
```

### 步驟 3: 開始使用

執行儲存格後：

1.  **觀察指揮中心**: 您會看到一個動態面板出現。
    *   **上半部分**：顯示系統狀態 (CPU/RAM) 和即時的事件日誌。所有依賴安裝、伺服器啟動的過程都會在這裡顯示。
    *   **下半部分**：一旦後端伺服器成功啟動，您的應用程式介面將會自動嵌入到這裡。
2.  **與應用互動**: 您可以直接在下半部分的 IFrame 中操作您的應用程式。
3.  **備用連結**: 如果 IFrame 無法正常顯示，面板中會提供一個備用連結，您可以在新的瀏覽器分頁中開啟它。
4.  **任務結束**: 當您完成操作後，可以點擊 Colab 儲存格左側的「停止」按鈕。指揮中心會自動進行清理工作，並將本次執行的完整日誌儲存到 `作戰日誌歸檔` 資料夾中。

## 故障排除

- **`找不到專案資料夾`**:
  - **原因**: `TARGET_FOLDER_NAME` 參數設定錯誤，或者您沒有將專案放置在預期的 `/content/` 目錄下。
  - **解決**: 請檢查 Colab 左側檔案總管中的資料夾名稱，並確保其與表單中的設定一致。
- **`找不到點火器腳本 'colab_run.py'`**:
  - **原因**: Colab 的工作目錄沒有被正確設定到您的專案根目錄，或者 `colab_run.py` 檔案遺失/損毀。
  - **解決**: 確保您的專案結構完整，並在執行儲存格之前，已透過 `os.chdir()` 切換到正確的目錄。上方的範本程式碼已包含此邏輯。
- **IFrame 無法顯示**:
  - **原因**: 可能是因為瀏覽器安全策略或網路問題。
  - **解決**: 使用面板中提供的「在新分頁中開啟」的備用連結。
- **伺服器啟動失敗**:
  - **原因**: 您的後端程式碼 (`main.py` 或 `apps` 中的邏輯) 可能存在錯誤。
  - **解決**: 仔細查看指揮中心上半部分的日誌輸出，紅色的 `ERROR` 或 `FATAL` 訊息會提供失敗的詳細原因。
