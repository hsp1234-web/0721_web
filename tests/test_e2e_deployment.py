# In tests/test_e2e_deployment.py
import pytest
import subprocess
import time
import requests
import psutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

@pytest.fixture(scope="module")
def live_server():
    # --- 抽象草圖：Setup ---
    # 1. 啟動 run.sh
    process = subprocess.Popen(
        ["bash", "run.sh"],
        cwd=PROJECT_ROOT,
    )
    # 2. 等待伺服器上線
    time.sleep(5)

    yield process # <-- 移交控制權

    # --- 抽象草圖：Teardown ---
    # 3. 清理戰場
    parent = psutil.Process(process.pid)
    for child in parent.children(recursive=True):
        child.terminate()
    parent.terminate()
    process.wait(timeout=5)

def test_deployment_script_launches_healthy_server(live_server):
    # 1. 發送健康探測
    response = requests.get("http://localhost:8000/")

    # 2. 驗證服務活性
    assert response.status_code == 200
    assert "<title>整合型應用平台</title>" in response.text

    # 3. 驗證核心資產已生成
    db_path = PROJECT_ROOT / "logs.sqlite"
    assert db_path.exists()
