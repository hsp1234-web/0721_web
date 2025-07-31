# -*- coding: utf-8 -*-
"""
語音轉寫 App 的 API 點火測試
"""
# -*- coding: utf-8 -*-
"""
語音轉寫 App 的 API 點火測試
"""
import io
import os
import sys
import time
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from apps.transcriber.main import app

# 設置導入路徑，確保可以找到 App 的主模組
# 我們需要將專案的根目錄 (包含 apps/ 和 tests/ 的目錄) 加入 sys.path
# 這樣 Python 才能找到 `transcriber` 模組
project_root = Path.cwd()
sys.path.insert(0, str(project_root))

# 使用 FastAPI 的測試客戶端
client = TestClient(app)

# --- 輔助函式 ---

def poll_for_status(task_id: str, timeout: int = 10) -> dict:
    """
    輪詢任務狀態，直到完成或超時。
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        response = client.get(f"/status/{task_id}")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "completed":
                return data
        time.sleep(0.5) # 避免過於頻繁的請求
    pytest.fail(f"輪詢任務 {task_id} 超時。")

# --- 測試案例 ---

def test_health_check():
    """
    測試 `/health` 端點是否正常工作。
    這是一個最基本的「點火測試」，確認伺服器可以啟動並回應請求。
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "語音轉寫服務運行中"}

def test_upload_and_get_status_mock_mode():
    """
    測試核心流程：上傳 -> 查詢狀態 -> 驗證結果 (模擬模式)
    """
    # 1. 準備一個模擬的音訊檔案
    # 在模擬模式下，檔案內容不重要，但檔案本身必須存在
    fake_audio_content = b"this is a fake wav file"
    fake_audio_file = ("test_audio.wav", io.BytesIO(fake_audio_content), "audio/wav")

    # 2. 呼叫 /upload 端點
    # 我們將 APP_MOCK_MODE 設為 "true" 來強制啟用模擬邏輯
    os.environ["APP_MOCK_MODE"] = "true"
    response = client.post("/upload", files={"file": fake_audio_file})
    del os.environ["APP_MOCK_MODE"] # 測試後清理環境變數

    # 3. 驗證上傳回應
    assert response.status_code == 202 # 202 Accepted
    upload_data = response.json()
    assert "task_id" in upload_data
    task_id = upload_data["task_id"]

    # 4. 輪詢狀態端點直到任務完成
    status_data = poll_for_status(task_id)

    # 5. 驗證最終結果
    assert status_data["status"] == "completed"
    assert status_data["mode"] == "mock"
    assert status_data["original_filename"] == "test_audio.wav"
    # 驗證結果是否為模擬邏輯中產生的格式
    expected_result = "這是 'test_audio.wav' 的模擬轉寫結果。"
    assert status_data["result"] == expected_result


# --- E2E 測試 ---

def create_dummy_wav_file(duration_ms: int = 100) -> io.BytesIO:
    """
    以程式化方式產生一個符合 WAV 格式的靜音音訊檔案。
    這樣就不需要在版本庫中儲存一個實體音訊檔。
    """
    # WAV 檔案頭部參數
    sample_rate = 16000  # 16kHz
    channels = 1         # 單聲道
    bits_per_sample = 16 # 16-bit
    byte_rate = sample_rate * channels * bits_per_sample // 8
    block_align = channels * bits_per_sample // 8
    num_samples = sample_rate * duration_ms // 1000
    data_size = num_samples * block_align
    file_size = 36 + data_size

    # 建立一個二進位資料流
    wav_file = io.BytesIO()

    # 寫入 WAV 檔案頭部
    wav_file.write(b'RIFF')
    wav_file.write(file_size.to_bytes(4, 'little'))
    wav_file.write(b'WAVE')
    wav_file.write(b'fmt ')
    wav_file.write((16).to_bytes(4, 'little')) # Sub-chunk 1 size
    wav_file.write((1).to_bytes(2, 'little'))  # Audio format (1 for PCM)
    wav_file.write(channels.to_bytes(2, 'little'))
    wav_file.write(sample_rate.to_bytes(4, 'little'))
    wav_file.write(byte_rate.to_bytes(4, 'little'))
    wav_file.write(block_align.to_bytes(2, 'little'))
    wav_file.write(bits_per_sample.to_bytes(2, 'little'))
    wav_file.write(b'data')
    wav_file.write(data_size.to_bytes(4, 'little'))

    # 寫入靜音音訊資料 (全為零)
    wav_file.write(b'\0' * data_size)

    # 將指標移回檔案開頭，以便 FastAPI 讀取
    wav_file.seek(0)
    return wav_file

@pytest.mark.skipif(
    os.environ.get("TEST_MODE", "mock") != "real",
    reason="此為 E2E 測試，只在 TEST_MODE=real 時運行。"
)
def test_upload_and_get_status_real_mode():
    """
    測試核心流程：上傳 -> 查詢狀態 -> 驗證結果 (真實模式)
    """
    # 1. 準備一個真實的 (但很小的) WAV 檔案
    real_audio_file_stream = create_dummy_wav_file()
    real_audio_file = ("test_real_audio.wav", real_audio_file_stream, "audio/wav")

    # 2. 呼叫 /upload 端點
    # 這次不設定 APP_MOCK_MODE，讓它走真實轉寫邏輯
    response = client.post("/upload", files={"file": real_audio_file})

    # 3. 驗證上傳回應
    assert response.status_code == 202
    upload_data = response.json()
    task_id = upload_data["task_id"]

    # 4. 輪詢狀態端點直到任務完成 (給予更長的超時時間)
    status_data = poll_for_status(task_id, timeout=60) # 真實模型需要更長時間

    # 5. 驗證最終結果
    assert status_data["status"] == "completed"
    assert status_data["mode"] == "real"
    assert status_data["original_filename"] == "test_real_audio.wav"
    # 在真實模式下，我們無法預測精確的轉寫結果 (特別是對於靜音)
    # 但我們可以斷言它不是 None，且是一個字串
    assert isinstance(status_data["result"], str)


def test_upload_without_file():
    """
    測試在沒有提供檔案的情況下呼叫 /upload 端點。
    FastAPI 會因為缺少必要的 `File` 部分而返回 422 錯誤。
    """
    response = client.post("/upload")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["msg"] == "Field required"

def test_status_not_found():
    """
    測試查詢一個不存在的任務 ID。
    預期會收到 404 Not Found 錯誤。
    """
    non_existent_task_id = "a-fake-task-id"
    response = client.get(f"/status/{non_existent_task_id}")
    assert response.status_code == 404
    assert response.json() == {"detail": f"找不到任務 ID: {non_existent_task_id}"}
