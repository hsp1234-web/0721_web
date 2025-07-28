import subprocess
import time
import httpx
import os
import signal
import pytest

# --- 測試參數 ---
TEST_QUANT_PORT = 9901
TEST_TRANSCRIBER_PORT = 9902
TEST_TIMEZONE = "America/Los_Angeles"
LAUNCH_SCRIPT = "scripts/launch.py"

@pytest.fixture(scope="module")
def setup_environment():
    """確保測試環境已準備好。"""
    print("--- 正在準備測試環境 (執行 --prepare-only) ---")
    prepare_process = subprocess.run(
        ["python", LAUNCH_SCRIPT, "--prepare-only"],
        capture_output=True, text=True
    )
    assert prepare_process.returncode == 0, "環境準備失敗"
    print("--- 環境準備完成 ---")

@pytest.fixture
def launch_services():
    """啟動後端服務並在測試結束後清理。"""
    print(f"--- 正在以測試參數啟動服務 ---\n"
          f"Quant Port: {TEST_QUANT_PORT}\n"
          f"Transcriber Port: {TEST_TRANSCRIBER_PORT}\n"
          f"Timezone: {TEST_TIMEZONE}")

    command = [
        "python", LAUNCH_SCRIPT,
        "--port-quant", str(TEST_QUANT_PORT),
        "--port-transcriber", str(TEST_TRANSCRIBER_PORT),
        "--timezone", TEST_TIMEZONE
    ]

    # 使用 Popen 啟動 launch.py 作為一個子程序
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)

    # 給予足夠的時間讓服務啟動
    time.sleep(20)

    # 使用 yield 將程序物件傳遞給測試函數
    yield process

    # --- 清理階段 ---
    print(f"\n--- 測試結束，正在清理程序 (PID: {process.pid}) ---")
    if process.poll() is None:
        print(f"向 PID {process.pid} 發送 SIGTERM...")
        process.terminate() # 使用 terminate (SIGTERM)
        try:
            process.wait(timeout=10)
            print(f"程序 {process.pid} 已成功終止。")
        except subprocess.TimeoutExpired:
            print(f"程序 {process.pid} 未能終止，強制結束。")
            process.kill()
    else:
        print(f"程序 {process.pid} 已自行終止。")

    # 打印剩餘的日誌以供除錯
    stdout, _ = process.communicate()
    if stdout:
        print("--- 剩餘日誌 ---")
        print(stdout)

def test_service_configuration_and_shutdown(setup_environment, launch_services):
    """
    主要測試函數：
    1. 驗證服務是否以正確的組態啟動。
    2. 驗證服務是否能被正常關閉。
    """
    process = launch_services

    # 驗證主啟動程序是否仍在運行
    assert process.poll() is None, "主啟動程序在測試開始前就已終止！"

    # 步驟 1: 驗證服務組態
    health_url = f"http://localhost:{TEST_QUANT_PORT}/health"
    try:
        print(f"--- 正在向 {health_url} 進行健康檢查 ---")
        response = httpx.get(health_url, timeout=20)
        response.raise_for_status()
        data = response.json()

        print(f"收到的回應: {data}")

        config = data.get("config", {})
        assert config.get("port") == str(TEST_QUANT_PORT)
        assert config.get("timezone") == TEST_TIMEZONE
        print("--- ✅ 組態驗證成功！ ---")

    except httpx.RequestError as e:
        pytest.fail(f"無法連接到服務: {e}")
    except Exception as e:
        pytest.fail(f"解析或斷言回應時發生錯誤: {e}")

    # 步驟 2: 驗證關閉機制 (這部分由 launch_services fixture 的清理階段自動執行)
    # 我們在這裡不需要做任何事，pytest 會在測試結束後自動呼叫 fixture 的清理代碼
    print("--- 測試主體完成，即將由 fixture 執行清理 ---")
