# 測試計畫與執行指南 (作戰藍圖 v3.0 - Pythonic)

**文件作者：** Jules (AI 軟體工程師)
**最後更新：** 2025年7月29日

## 一、 核心理念：快速、穩健、平行的 Pythonic 測試

為了解決傳統測試流程的瓶頸，我們已將測試框架全面升級為一個以 Python 為核心的現代化解決方案。此框架被固化在一個名為 `smart_e2e_test.py` 的統一指揮腳本中，它徹底解決了空間、時間與穩定性的三重困境。

### **核心優勢：**

1.  **極致速度 (解決時間瓶頸):**
    *   **應用級平行 (App-level Parallelism):** 利用 Python 的 `multiprocessing` 模組，可以同時對多個獨立的 App (如 `quant`, `transcriber`) 執行完整的測試流程。
    *   **測試級平行 (Test-level Parallelism):** 在每個 App 的測試流程內部，利用 `pytest-xdist` 將測試案例分配到所有可用的 CPU 核心，實現最大程度的平行化。

2.  **絕對穩定 (解決穩定性瓶頸):**
    *   **主動超時中斷:** 透過整合 `pytest-timeout`，為每一個測試案例都設定了 300 秒的「生命時鐘」。任何因意外情況（如外部 API 無回應、死循環）而卡死的測試都會被自動中斷並標記為失敗，確保整個 CI/CD 流程永遠不會被無限期阻塞。

3.  **資源高效 (解決空間瓶頸):**
    *   **原子化隔離:** 每個 App 的測試都在一個獨立的、用後即焚的虛擬環境中執行。測試結束後，該環境會被徹底刪除，將硬碟空間 100% 釋放，確保資源峰值佔用永遠在可控範圍內。
    *   **跨平台兼容:** 作為一個純 Python 腳本，它可以在 Windows, macOS, Linux, 以及 Google Colab 等任何支持 Python 的環境中無縫運行。

---

## 二、 如何執行測試：`smart_e2e_test.py`

所有端對端測試都應透過根目錄下的 `smart_e2e_test.py` 腳本來啟動。

### **前置要求：**

- **Python 3.8+ 環境：** 腳本會自動安裝 `uv`, `psutil`, `pyyaml` 等核心依賴。
- **網路連線：** 用於下載依賴套件。

### **基本用法 (模擬模式):**

在專案的根目錄下，使用 Python 解譯器執行腳本：

```bash
python smart_e2e_test.py
```

預設情況下，這將以 `TEST_MODE=mock` (模擬模式) 運行所有測試。在模擬模式下，腳本會**跳過**大型依賴（如 `torch`）的下載和安裝，並執行快速的 API 路徑驗證，主要用於開發過程中的快速反饋。

### **進階用法 (真實模式):**

若需驗證包含大型 AI 模型在內的完整功能（例如，在部署前或修改了核心轉錄邏輯後），可透過設定環境變數 `TEST_MODE` 來啟用「真實模式」。

**Linux / macOS:**
```bash
TEST_MODE=real python smart_e2e_test.py
```

**Windows (CMD):**
```cmd
set TEST_MODE=real
python smart_e2e_test.py
```

**Windows (PowerShell):**
```powershell
$env:TEST_MODE="real"
python smart_e2e_test.py
```

---

## 三、 Colab 一鍵驗證

對於需要快速驗證整個系統是否正常運行的使用者，我們提供了 `colab_dashboard_test.ipynb`。

只需在 Google Colab 中打開此 Notebook，並依序執行其中的儲存格，即可自動完成以下所有操作：
1.  下載最新程式碼。
2.  執行完整的端對端測試 (`smart_e2e_test.py`)。
3.  在背景啟動所有後端服務。
4.  驗證核心的逆向代理服務是否正常運行。

這提供了一個極其便利的方式來驗證部署的最終狀態。
