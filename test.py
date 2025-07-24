# -*- coding: utf-8 -*-
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

# --- 常數設定 ---
HOST = "127.0.0.1"
PORT = 8765
APPS_API_URL = f"http://{HOST}:{PORT}/api/apps"
STARTUP_TIMEOUT = 20  # 秒，新架構應該能快速啟動
SHUTDOWN_TIMEOUT = 10

def print_test_step(message: str):
    """打印格式化的測試步驟標題。"""
    print(f"\n{'='*60}")
    print(f"🧪 {message}")
    print(f"{'='*60}")

def test_server_startup(process):
    """
    測試伺服器是否能成功啟動並正確加載 Apps。
    """
    import requests
    print_test_step(f"測試伺服器啟動與 App 加載 ({APPS_API_URL})")
    start_time = time.time()
    while time.time() - start_time < STARTUP_TIMEOUT:
        try:
            response = requests.get(APPS_API_URL, timeout=2)
            if response.status_code == 200:
                apps = response.json()
                print(f"✅ 成功: API 回傳 200 OK。")
                print(f"✅ 成功: 伺服器在 {time.time() - start_time:.2f} 秒內成功啟動。")

                # 驗證是否成功加載了我們建立的兩個 App
                app_ids = {app.get('id') for app in apps}
                if "transcriber" in app_ids and "quant" in app_ids:
                    print(f"✅ 成功: 成功檢測到 'transcriber' 和 'quant' 應用。")
                    return True
                else:
                    print(f"❌ 失敗: API 回傳的應用列表不完整: {app_ids}", file=sys.stderr)
                    return False
        except requests.exceptions.RequestException as e:
            print(f"🟡 警告: 連線到伺服器失敗 ({e.__class__.__name__})，重試中...")

        if process.poll() is not None:
            print(f"❌ 失敗: 伺服器進程在啟動期間意外終止，返回碼: {process.poll()}", file=sys.stderr)
            return False

        time.sleep(1)

    print(f"❌ 失敗: 伺服器未能在 {STARTUP_TIMEOUT} 秒內就緒。", file=sys.stderr)
    return False

def test_server_shutdown(process):
    """
    測試伺服器是否能透過 SIGINT 優雅關閉。
    """
    print_test_step("測試伺服器優雅關閉 (SIGINT)")

    print(f"INFO: 向進程 {process.pid} 發送 SIGINT 訊號...")
    if sys.platform == "win32":
        process.send_signal(signal.CTRL_C_EVENT)
    else:
        process.send_signal(signal.SIGINT)

    try:
        process.wait(timeout=SHUTDOWN_TIMEOUT)
        print(f"✅ 成功: 伺服器進程已在 {SHUTDOWN_TIMEOUT} 秒內成功關閉。")
        return True
    except subprocess.TimeoutExpired:
        print(f"❌ 失敗: 伺服器進程未能於 {SHUTDOWN_TIMEOUT} 秒內終止。", file=sys.stderr)
        print("INFO: 強制終止進程...")
        process.kill()
        return False

def main():
    """整合測試主函式。"""
    print_test_step("執行依賴安裝")
    install_command = [sys.executable, "run.py", "--install-only"]
    install_result = subprocess.run(install_command)
    if install_result.returncode != 0:
        print("❌ 失敗: 依賴安裝失敗，測試終止。", file=sys.stderr)
        sys.exit(1)
    print("✅ 成功: 依賴安裝完成。")

    print_test_step("啟動伺服器子進程")
    run_command = [sys.executable, "run.py", "--run-only", f"--port={PORT}", f"--host={HOST}"]

    # 在 Windows 上，需要設定 creationflags 以避免將 Ctrl+C 傳遞給子進程
    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0

    process = subprocess.Popen(
        run_command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        creationflags=creationflags
    )

    time.sleep(2) # 給予進程一些初始化時間

    # 執行測試
    try:
        startup_ok = test_server_startup(process)
        shutdown_ok = False
        if startup_ok:
            shutdown_ok = test_server_shutdown(process)
        else:
            print("INFO: 因啟動失敗，跳過關閉測試。")
    finally:
        # 確保子進程在任何情況下都會被終止
        if process.poll() is None:
            print("INFO: 測試結束，強制終止殘餘的伺服器進程...")
            process.kill()

        # 打印伺服器的輸出以便調試
        print("\n--- 伺服器 STDOUT ---")
        print(process.stdout.read())
        print("--- 伺服器 STDERR ---")
        print(process.stderr.read())
        print("--------------------")

    # 報告最終結果
    print("\n====================================")
    if startup_ok and shutdown_ok:
        print("✅✅✅ 所有測試均已通過！新架構穩定。 ✅✅✅")
    else:
        print("❌❌❌ 部分或全部測試失敗。 ❌❌❌")
        sys.exit(1)

if __name__ == "__main__":
    main()
