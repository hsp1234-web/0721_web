# Colab 使用指南：統一指揮中心

## 簡介

歡迎使用「統一指揮中心」！本平台專為在 Google Colab 環境中穩定、可靠地運行 Web 服務而設計。透過我們提供的 Colab 筆記本，您可以一鍵啟動您的服務。

平台會自動處理：
*   使用 `uv` 進行高速依賴安裝。
*   啟動後端 FastAPI 服務。
*   使用 Google Colab 的內建代理功能，為您的應用程式生成一個安全、私有的訪問連結。

## Colab 啟動介面

將下方的程式碼儲存格複製到您的 Colab 筆記本中。執行後，它將會安裝依賴並啟動服務。

### 如何設定

在執行儲存格之前，請根據您的需求設定以下參數：

*   `PROJECT_FOLDER_NAME`: 這是您存放整個專案的資料夾名稱。例如：`MP3_Converter_TXT`。
*   `FASTAPI_PORT`: 您的後端 FastAPI 應用程式將在此埠號上運行。預設值為 `8000`。

### 啟動儲存格程式碼

<details>
<summary>點此展開/收合 🚀 啟動指揮中心 的程式碼</summary>

```python
#@title 🚀 啟動指揮中心 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **專案路徑與伺服器設定**
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "ALL_DATE/MP3_Converter_TXT" #@param {type:"string"}
#@markdown **後端服務埠號 (FASTAPI_PORT)**
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
import subprocess

# --- 步驟 1: 切換路徑並驗證 ---
project_path = Path(f"/content/{PROJECT_FOLDER_NAME}")
if not project_path.is_dir():
    print(f"❌ 致命錯誤：找不到專案資料夾 '{project_path}'。")
else:
    os.chdir(project_path)
    print(f"✅ 工作目錄已切換至: {os.getcwd()}")

    # --- 步驟 2: 安裝依賴 ---
    # 我們將安裝所有必要的依賴，以便在 Colab 中運行
    print("--- 正在安裝核心、轉錄及測試依賴 ---")
    try:
        # 使用 uv 來加速安裝
        subprocess.run(["pip", "install", "uv"], check=True)
        # 安裝運行所需的所有 requirements
        subprocess.run(["uv", "pip", "install", "-r", "requirements/base.txt"], check=True)
        subprocess.run(["uv", "pip", "install", "-r", "requirements/transcriber.txt"], check=True)
        print("✅ 依賴安裝完成。")

        # --- 步驟 3: 啟動服務 ---
        print(f"--- 準備在埠號 {FASTAPI_PORT} 上啟動 FastAPI 服務 ---")
        print("您將在下方看到一個 `https://*.loca.lt` 或類似的公開連結。")

        # 使用 uvicorn 啟動位於 src/main.py 的 FastAPI 應用
        # 注意：假設您的 FastAPI app 物件在 src/main.py 中被命名為 'app'
        subprocess.run([
            "uvicorn",
            "src.main:app",
            "--host", "0.0.0.0",
            "--port", str(FASTAPI_PORT),
            "--reload"  # 在 Colab 中使用 reload 可能有助於開發
        ])

    except subprocess.CalledProcessError as e:
        print(f"❌ 執行命令時發生錯誤: {e}")
    except Exception as e:
        import traceback
        print(f"💥 執行期間發生未預期的嚴重錯誤: {e}")
        traceback.print_exc()

```
</details>

## 執行與訪問

1.  **設定參數**：根據您的專案位置，填寫 `PROJECT_FOLDER_NAME` 欄位。
2.  **執行儲存格**：點擊儲存格左側的「播放」按鈕。
3.  **訪問應用**：當後端服務完全上線後，Colab 會在儲存格輸出中生成一個可點擊的應用程式連結 (通常以 `https://` 開頭)。點擊該連結，即可在新分頁中與您的應用程式互動。
