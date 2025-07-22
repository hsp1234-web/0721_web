import requests
import time
from pathlib import Path
import pytest
import os

# --- 測試設定 ---
BASE_URL = "http://127.0.0.1:8000"
# 在專案根目錄下尋找測試音訊檔案
TEST_AUDIO_PATH = Path(__file__).parent.parent.parent.parent / "tests" / "test_audio.wav"

@pytest.fixture(scope="module")
def server_is_ready():
    """一個 fixture，用來檢查伺服器是否已準備好接收請求。"""
    start_time = time.time()
    while time.time() - start_time < 120:  # 120 秒超時
        try:
            response = requests.get(f"{BASE_URL}/api/apps")
            if response.status_code == 200:
                return True
        except requests.ConnectionError:
            time.sleep(1)
    pytest.fail("伺服器在 120 秒內未能啟動。")

@pytest.mark.e2e
def test_full_transcription_flow(server_is_ready):
    """
    測試從上傳音訊檔案到獲取非空轉寫結果的完整端對端流程。
    """
    # 1. 準備音訊檔案
    if not TEST_AUDIO_PATH.exists():
        # 如果音訊檔案不存在，我們需要創建一個。
        # 這裡我們使用一個簡單的方法來創建一個假的 WAV 檔案。
        # 在真實的場景中，這裡應該是一個真實的、簡短的音訊檔案。
        from scipy.io.wavfile import write
        import numpy as np
        samplerate = 44100
        duration = 1
        frequency = 440
        t = np.linspace(0., duration, int(samplerate * duration))
        amplitude = np.iinfo(np.int16).max * 0.5
        data = amplitude * np.sin(2. * np.pi * frequency * t)
        write(TEST_AUDIO_PATH, samplerate, data.astype(np.int16))

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
            # 4. 驗證結果
            assert "result" in status_data
            assert "text" in status_data["result"]
            assert status_data["result"]["text"] != ""
            # 測試成功，跳出迴圈
            return
        elif status_data["status"] == "failed":
            pytest.fail(f"轉寫任務失敗: {status_data.get('error', '未知錯誤')}")

        time.sleep(2)  # 等待 2 秒後再次查詢

    pytest.fail("在 120 秒的超時時間內，轉寫任務未能完成。")
