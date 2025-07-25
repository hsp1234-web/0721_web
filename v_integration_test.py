# ==============================================================================
#                 端到端整合測試腳本 (E2E Integration Test)
#
#   Jules，此腳本用於對 `colab_run.py` 的完整啟動流程進行自動化驗證。
#
#   測試流程：
#   1. 準備一個 LogCaptureHandler 來捕獲所有通過 PrecisionIndicator 的日誌。
#   2. 在一個獨立的執行緒中，啟動 `colab_run.main` 函式。
#   3. 等待一段預設的時間（例如 20 秒），讓安裝依賴、啟動伺服器等流程完成。
#   4. 檢查 LogCaptureHandler 中捕獲的日誌，斷言 (assert) 關鍵的啟動步驟訊息
#      都已按預期出現。
#   5. 使用 httpx 向本地啟動的伺服器發送一個 GET 請求，斷言其返回 200 OK，
#      以證明後端服務真實可用。
#   6. 發送停止訊號，安全地終止所有相關進程和執行緒。
#   7. 如果所有斷言都通過，腳本會以返回碼 0 正常退出。
#
# ==============================================================================

import time
import threading
import sys
from pathlib import Path
import httpx

# --- 環境設定 ---
# 調整 sys.path 以便能夠匯入專案模組
sys.path.append(str(Path(__file__).parent))

# 匯入需要測試的目標模組和我們新增的測試工具
# 注意：我們需要模擬 colab_run 中的 STOP_EVENT
from colab_run import main as colab_main, LogCaptureHandler, STOP_EVENT

# --- 測試組態 ---
TEST_DURATION_SECONDS = 25  # 給予足夠的時間讓所有流程（包括依賴安裝）完成
SERVER_URL = "http://127.0.0.1:8000/docs"

def run_colab_main_in_thread(config, log_handler):
    """在一個執行緒中執行 colab_main。"""

    # 修改 config 以注入我們的日誌處理器
    config['extra_handlers'] = [log_handler]

    try:
        colab_main(config)
    except Exception as e:
        print(f"[TEST_RUNNER] colab_main 執行緒中發生錯誤: {e}")

def main():
    print("--- 🎬 啟動端到端整合測試 ---")

    # 1. 準備日誌捕獲器
    log_capture_handler = LogCaptureHandler()

    # 2. 準備 colab_main 的設定
    colab_config = {
        # 使用純 ASCII 路徑以避免在某些測試環境中出現編碼問題
        "archive_folder_name": "test_archive_logs",
        "fastapi_port": 8000,
    }

    # 3. 在獨立執行緒中啟動 `colab_run.main`
    print(f"[*] 正在背景啟動 colab_run.main，將運行 {TEST_DURATION_SECONDS} 秒...")
    main_thread = threading.Thread(
        target=run_colab_main_in_thread,
        args=(colab_config, log_capture_handler)
    )
    main_thread.daemon = True
    main_thread.start()

    # 4. 等待啟動流程完成
    time.sleep(TEST_DURATION_SECONDS)

    # 5. 停止所有流程
    print("[*] 測試時間到，正在發送停止訊號...")
    STOP_EVENT.set()
    main_thread.join(timeout=10) # 等待主執行緒優雅退出
    print("[*] 所有背景進程已停止。")

    # 6. 執行斷言 (Assertions)
    print("\n--- 🧐 開始執行驗證 ---")
    captured_logs_str = "\n".join(log_capture_handler.records)

    # 斷言 6.1: 檢查關鍵日誌是否存在
    print("[*] 正在驗證日誌記錄...")
    key_log_messages = [
        "作戰流程啟動：正在安裝/驗證專案依賴...",
        "正在使用 'uv' 安裝 'requirements.txt'...",
        "專案依賴已成功配置。",
        "正在啟動主應用伺服器...",
        "準備啟動儀表板...",
        "服務連結已生成。",
        "作戰系統已上線！",
    ]

    all_logs_found = True
    for msg in key_log_messages:
        try:
            assert msg in captured_logs_str
            print(f"  ✅ 找到日誌: '{msg[:40]}...'")
        except AssertionError:
            print(f"  ❌ 遺失日誌: '{msg[:40]}...'")
            all_logs_found = False

    assert all_logs_found, "一個或多個關鍵日誌未能在輸出中找到！"
    print("✅ 所有關鍵日誌均已找到。")

    # 斷言 6.2: 檢查後端伺服器是否真實可達
    print("\n[*] 正在驗證後端伺服器連線...")
    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(SERVER_URL)
            response.raise_for_status() # 如果狀態碼不是 2xx，則會引發異常
            assert "FastAPI" in response.text, "預期的 FastAPI 文件頁面內容未找到！"
        print(f"✅ 成功連接到 {SERVER_URL} (狀態碼: {response.status_code}) 並驗證內容。")
    except httpx.RequestError as e:
        print(f"❌ 連接到後端伺服器失敗: {e}")
        assert False, "無法連接到後端伺服器。"
    except AssertionError as e:
        print(f"❌ 伺服器回應內容不正確: {e}")
        assert False, "伺服器回應內容不正確。"

    print("\n--- ✅ 端到端整合測試成功 ---")

if __name__ == "__main__":
    main()
