# Colab 使用者指南：鳳凰之心作戰平台

## 簡介

歡迎使用「鳳凰之心」作戰平台！本平台專為在 Google Colab 環境中穩定、可靠地運行 Web 服務而設計。透過我們提供的 Colab 筆記本，您可以透過一個簡單的表單介面來設定並一鍵啟動您的服務。

平台會自動處理：

*   使用 `uv` 進行高速依賴安裝。
*   啟動後端 FastAPI 服務。
*   **在 Colab 儲存格中直接渲染一個全功能的純文字儀表板，即時監控系統狀態。**
*   使用 Google Colab 的內建代理功能，為您的應用程式生成一個**安全、私有**的訪問連結。

## Colab 啟動介面

將下方的程式碼儲存格複製到您的 Colab 筆記本中。執行後，您會看到一個可互動的表單。

### 如何設定

在執行儲存格之前，請根據您的需求設定以下參數：

*   `PROJECT_FOLDER_NAME`: 這是您存放整個專案的資料夾名稱。
    *   如果您是透過 `git clone https://github.com/user/repo.git WEB` 克隆的，那這裡就填 `WEB`。
    *   如果您將專案放在 Google Drive 的 `MyDrive/MyProject` 中，並已掛載 Drive，那這裡就填 `drive/MyDrive/MyProject`。
*   `ARCHIVE_FOLDER_NAME`: 當您停止服務時，所有詳細的執行日誌會被打包成一個 `.txt` 檔案，並儲存在以此命名的資料夾中。
*   `FASTAPI_PORT`: 您的後端 FastAPI 應用程式將在此埠號上運行。`colab_run.py` 會將這個埠號暴露給 Colab 的代理。預設值為 `8000`。

### 啟動儲存格程式碼 (v16.0 - 儀表板版)

<details>
<summary>點此展開/收合 🚀 啟動鳳凰之心儀表板指揮中心 的程式碼</summary>

```python
#@title 💎 鳳凰之心儀表板指揮中心 v16.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **專案路徑與伺服器設定**
#@markdown > **請指定要執行後端程式碼的資料夾名稱。**
#@markdown ---
#@markdown **指定專案資料夾名稱 (PROJECT_FOLDER_NAME)**
#@markdown > **請輸入包含您後端程式碼 (例如 `main.py`, `colab_run.py`) 的資料夾名稱。例如：`WEB`。**
PROJECT_FOLDER_NAME = "WEB" #@param {type:"string"}
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
# 注意：舊的顯示參數已被移除，因為儀表板現在是固定佈局
config = {
    "archive_folder_name": ARCHIVE_FOLDER_NAME,
    "fastapi_port": FASTAPI_PORT,
}

# --- 步驟 2: 切換路徑並驗證 ---
project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")
if not project_path.is_dir():
    print(f"❌ 致命錯誤：找不到專案資料夾 '{project_path}'。")
    print(f"   請確認您已將專案上傳或 clone 到正確的位置，並且 PROJECT_FOLDER_NAME 設定正確。")
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
    finally:
        # --- 步驟 4: 最終歸檔複製 ---
        print("\n--- 正在執行最終歸檔複製... ---")
        try:
            import shutil

            # 動態構建源路徑(在專案資料夾內)和目標路徑(在/content根目錄下)
            source_dir = project_path / ARCHIVE_FOLDER_NAME
            destination_dir = Path("/content") / ARCHIVE_FOLDER_NAME

            if source_dir.is_dir():
                if destination_dir.exists():
                    shutil.rmtree(destination_dir)
                shutil.copytree(source_dir, destination_dir)
                print(f"✅ 成功將 '{source_dir.name}' 複製到 /content 目錄下。")
            else:
                print(f"⚠️ 警告：在專案資料夾中找不到歸檔目錄 '{source_dir}'，跳過複製。")
        except Exception as e:
            print(f"❌ 複製歸檔時發生錯誤: {e}")

```
</details>

## 執行與訪問

1.  **設定參數**：根據您的專案位置和偏好，填寫表單中的欄位。
2.  **執行儲存格**：點擊儲存格左側的「播放」按鈕。
3.  **查看儀表板**：程式將開始執行，儲存格的輸出會被一個動態的、持續更新的**純文字儀表板**所取代。您可以在此處即時監控：
    *   CPU 和 RAM 使用率。
    *   核心服務的運行狀態。
    *   最新的關鍵日誌。
4.  **訪問應用**：當後端服務完全上線後 (`colab_run.py` 會打印相關日誌)，Colab 會在儀表板下方生成一個可點擊的應用程式連結 (`https://*.gradio.live` 或 `https://*.loca.lt`)。

    > 👇 您的應用程式連結將會出現在儀表板下方。

點擊該連結，即可在新分頁中與您的應用程式互動。
