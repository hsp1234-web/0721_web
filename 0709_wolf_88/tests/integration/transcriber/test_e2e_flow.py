"""端到端流程測試"""
from __future__ import annotations

import asyncio
import time
from pathlib import Path

import httpx
import pytest

# --- 常數 ---
POLL_INTERVAL = 1  # 輪詢間隔（秒）
TEST_TIMEOUT = 30  # 測試總超時時間（秒）


@pytest.mark.asyncio
async def test_full_transcription_flow_with_mock_worker(live_api_server: str) -> None:
    """
    一個完整的端到端測試案例，使用模擬工人（Mock Worker）。

    1. 上傳一個假的音訊檔案並獲取 task_id。
    2. 輪詢狀態 API，直到任務狀態變為 'completed' 或 'failed'。
    3. 驗證最終的任務狀態和轉寫結果是否符合預期。
    """
    base_url = live_api_server
    start_time = time.time()

    # --- 步驟 1: 上傳一個假的音訊檔案 ---
    # 這個檔案的內容不重要，因為模擬工人不會真的處理它。
    mock_audio_path = Path("test_audio.wav")
    mock_audio_path.write_text("fake audio data")

    task_id = None
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            with mock_audio_path.open("rb") as f:
                files = {"file": (mock_audio_path.name, f, "audio/wav")}
                response = await client.post(f"{base_url}/upload", files=files)

        response.raise_for_status()
        assert response.status_code == 202

        response_data = response.json()
        assert "task_id" in response_data
        task_id = response_data["task_id"]
        print(f"測試任務 ID: {task_id}")

        # --- 步驟 2: 輪詢狀態 API ---
        final_status_data = None
        while time.time() - start_time < TEST_TIMEOUT:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(f"{base_url}/status/{task_id}")

            response.raise_for_status()
            status_data = response.json()
            current_status = status_data.get("status")
            print(f"當前任務狀態: {current_status}")

            if current_status in ["completed", "failed"]:
                final_status_data = status_data
                break

            await asyncio.sleep(POLL_INTERVAL)
        else:
            pytest.fail(
                f"測試在 {TEST_TIMEOUT} 秒後超時，任務未達到 'completed' 或 'failed' 狀態。"
            )

        # --- 步驟 3: 驗證最終結果 ---
        assert final_status_data is not None, "輪詢結束後未獲得最終狀態。"
        assert final_status_data["status"] == "completed"
        assert "這是一個模擬的轉寫結果" in final_status_data.get("result_text", "")

    finally:
        # 清理測試檔案
        if mock_audio_path.exists():
            mock_audio_path.unlink()
