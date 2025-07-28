import subprocess
import time
import httpx
import os
import signal

# --- 設定 ---
DASHBOARD_URL = "http://localhost:8080"
MAX_RETRIES = 10
RETRY_DELAY = 2  # 秒

def test_dashboard_startup_and_shutdown():
    """
    測試儀表板的啟動、網頁存取及關閉流程。
    """
    print("--- 開始儀表板端對端測試 ---")

    # 步驟 1: 使用 Popen 啟動儀表板，以便取得其 PID
    print(f"🚀 正在啟動儀表板...")
    command = ["python", "scripts/launch.py", "--dashboard"]

    # 使用 preexec_fn=os.setsid 創建一個新的 process group
    # 這樣我們就可以一次殺掉整個 gotty process tree
    process = subprocess.Popen(command, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    print(f"📊 儀表板程序已啟動 (PID: {process.pid})")

    try:
        # 步驟 2: 等待儀表板完全啟動
        print(f"⏳ 等待儀表板在 {DASHBOARD_URL} 上線...")
        for i in range(MAX_RETRIES):
            try:
                response = httpx.get(DASHBOARD_URL, timeout=5)
                # 檢查 HTTP 狀態碼
                if response.status_code == 200:
                    print(f"✅ 儀表板已上線！狀態碼: {response.status_code}")
                    # 步驟 3: 驗證儀表板內容
                    if "<title>GoTTY</title>" in response.text:
                        print("✅ 網頁內容驗證成功，包含 '<title>GoTTY</title>'。")
                        break
                    else:
                        # 為了除錯，印出部分的 response text
                        print(f"網頁內容不符合預期。部分內容: {response.text[:200]}")
                        raise ValueError("網頁內容不符合預期。")
            except (httpx.ConnectError, httpx.ReadTimeout) as e:
                print(f"嘗試 {i+1}/{MAX_RETRIES}: 連接失敗 ({e})，{RETRY_DELAY} 秒後重試...")
                time.sleep(RETRY_DELAY)
        else:
            # 如果迴圈正常結束 (沒有被 break)，表示超時
            raise RuntimeError(f"❌ 儀表板在 {MAX_RETRIES * RETRY_DELAY} 秒後仍未上線。")

        # 讓儀表板運行幾秒鐘，模擬觀察
        print("🎨 儀表板正在顯示漂亮的畫面... (等待 5 秒)")
        time.sleep(5)

    finally:
        # 步驟 4: 優雅地關閉儀表板及其所有子程序
        print(f"🛑 正在關閉儀表板程序 (PGID: {os.getpgid(process.pid)})...")
        # 使用 os.killpg 來關閉整個 process group
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)

        # 等待程序終止
        process.wait(timeout=10)
        print("✅ 儀表板程序已成功關閉。")

        # 檢查日誌
        stdout, stderr = process.communicate()
        print("\n--- 儀表板程序輸出 (stdout) ---")
        print(stdout)
        print("\n--- 儀表板程序輸出 (stderr) ---")
        print(stderr)

        if "Traceback" in stderr:
             raise AssertionError("❌ 儀表板關閉時在 stderr 中發現了 Traceback！")

        print("\n✅ 日誌檢查完畢，無嚴重錯誤。")

    print("\n🎉 儀表板端對端測試成功！")

if __name__ == "__main__":
    test_dashboard_startup_and_shutdown()
