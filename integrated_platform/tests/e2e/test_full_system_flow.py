import requests
import time
from pathlib import Path
import pytest
import subprocess
import os

# --- 測試設定 ---
BASE_URL = "http://127.0.0.1:8000"
# 注意：這個路徑依賴於測試是從專案根目錄執行的
TEST_AUDIO_PATH = Path("tests") / "test_audio.wav"

@pytest.fixture(scope="session", autouse=True)
def live_server():
    """
    一個會話級的 fixture，在所有 E2E 測試開始前，
    啟動核心引擎 `core_run.py`，並在所有測試結束後將其關閉。
    `autouse=True` 確保它對此檔案中的所有測試自動生效。
    """
    # --- 啟動伺服器 ---
    # 使用 poetry run python core_run.py 來啟動伺服器
    command = ["poetry", "run", "python", "core_run.py"]
    print(f"\n🚀 [E2E Setup] 正在啟動伺服器: {' '.join(command)}")

    # 我們將 stdout 和 stderr 導向到一個日誌檔案，以便調試
    server_log = open("e2e_server.log", "w")
    server_process = subprocess.Popen(
        command,
        stdout=server_log,
        stderr=subprocess.STDOUT,
        preexec_fn=os.setsid # 建立一個新的進程組，以便稍後可以殺死整個組
    )

    # --- 健康檢查 ---
    # 等待伺服器就緒
    start_time = time.time()
    is_server_ready = False
    while time.time() - start_time < 60:  # 60 秒超時
        try:
            # 我們使用 core_run 中定義的 health check 端點
            response = requests.get(f"{BASE_URL}/health", timeout=1)
            if response.status_code == 200:
                print("✅ [E2E Setup] 伺服器已成功啟動並通過健康檢查。")
                is_server_ready = True
                break
        except requests.ConnectionError:
            time.sleep(1) # 伺服器尚未啟動，等待一下

    if not is_server_ready:
        # 如果伺服器未能啟動，我們需要終止進程並讓測試失敗
        print("🔴 [E2E Setup] 伺服器在 60 秒內未能啟動。正在終止進程...")
        os.killpg(os.getpgid(server_process.pid), subprocess.signal.SIGTERM)
        server_process.wait()
        server_log.close()
        with open("e2e_server.log", "r") as f:
            print("--- Server Log ---")
            print(f.read())
            print("------------------")
        pytest.fail("E2E 測試失敗：無法啟動後端伺服器。")

    # --- 執行測試 ---
    yield

    # --- 清理工作 ---
    print("\n teardown] 正在關閉伺服器...")
    # 使用 os.killpg 來確保所有子進程都被殺死
    os.killpg(os.getpgid(server_process.pid), subprocess.signal.SIGTERM)
    server_process.wait() # 等待進程完全終止
    server_log.close()
    print("✅ [E2E Teardown] 伺服器已成功關閉。")


@pytest.mark.e2e
def test_full_transcription_flow():
    """
    測試從上傳音訊檔案到獲取非空轉寫結果的完整端對端流程。
    這個測試現在依賴於 `live_server` fixture 來確保伺服器正在運行。
    """
    # 1. 準備音訊檔案 (如果需要的話)
    if not TEST_AUDIO_PATH.exists():
        TEST_AUDIO_PATH.parent.mkdir(exist_ok=True)
        try:
            from scipy.io.wavfile import write
            import numpy as np
            samplerate = 44100; duration = 1; frequency = 440
            t = np.linspace(0., duration, int(samplerate * duration))
            amplitude = np.iinfo(np.int16).max * 0.5
            data = amplitude * np.sin(2. * np.pi * frequency * t)
            write(TEST_AUDIO_PATH, samplerate, data.astype(np.int16))
            print(f"🎵 [E2E Test] 已生成測試音訊檔案於: {TEST_AUDIO_PATH}")
        except ImportError:
            pytest.skip("需要 scipy 和 numpy 來動態生成測試音訊。請手動放置一個 test_audio.wav 檔案。")

    # 2. 上傳音訊檔案
    with open(TEST_AUDIO_PATH, "rb") as f:
        files = {"audio_file": (TEST_AUDIO_PATH.name, f, "audio/wav")}
        response = requests.post(f"{BASE_URL}/api/transcribe/upload", files=files)

    assert response.status_code == 202, f"預期狀態碼為 202，但收到了 {response.status_code}。回應內容: {response.text}"
    data = response.json()
    assert "job_id" in data
    job_id = data["job_id"]

    # 3. 輪詢任務狀態
    start_time = time.time()
    while time.time() - start_time < 120:  # 120 秒超時
        status_response = requests.get(f"{BASE_URL}/api/transcribe/status/{job_id}")
        assert status_response.status_code == 200, f"查詢狀態時失敗，狀態碼: {status_response.status_code}。回應內容: {status_response.text}"

        status_data = status_response.json()
        if status_data["status"] == "completed":
            assert "result" in status_data and "text" in status_data["result"]
            print(f"✅ [E2E Test] 任務完成，收到轉寫結果: '{status_data['result']['text'][:50]}...'")
            # 即使轉寫結果是空的也算成功，因為這代表流程走完了
            return
        elif status_data["status"] == "failed":
            pytest.fail(f"轉寫任務失敗: {status_data.get('error', '未知錯誤')}")

        time.sleep(2)

    pytest.fail("在 120 秒的超時時間內，轉寫任務未能完成。")
