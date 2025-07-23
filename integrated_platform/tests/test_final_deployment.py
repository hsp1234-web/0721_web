import subprocess
import pytest
from pathlib import Path
import os
import shutil
import sys
import re

# 獲取專案的根目錄
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

@pytest.fixture
def final_colab_env(tmp_path):
    """
    建立一個最終的、最真實的模擬 Colab 環境。
    結構必須與真實專案完全一致。
    - /tmp_path/content/WEB/
      - run.sh
      - pyproject.toml
      - poetry.lock
      - integrated_platform/
        - src/
          - ...
    """
    # 模擬 /content/WEB 作為專案根目錄
    project_dir = tmp_path / "content" / "WEB"
    project_dir.mkdir(parents=True)

    # 複製專案設定檔和啟動腳本到模擬的專案根目錄
    shutil.copy(PROJECT_ROOT / "run.sh", project_dir)
    shutil.copy(PROJECT_ROOT / "pyproject.toml", project_dir)
    shutil.copy(PROJECT_ROOT / "poetry.lock", project_dir)

    # 複製整個 `integrated_platform` 資料夾到模擬的專案根目錄
    shutil.copytree(PROJECT_ROOT / "integrated_platform", project_dir / "integrated_platform")

    # 返回 content 目錄和專案目錄
    return tmp_path / "content", project_dir

def test_final_run_sh_in_simulated_colab_env(final_colab_env):
    """
    驗證：使用最終版的 run.sh，在一個模擬的 Colab 環境中執行，
    應該能成功完成所有階段，並且 poetry 不會建立 venv。
    """
    content_dir, project_dir = final_colab_env

    # 模擬 Colab 環境變數
    env = os.environ.copy()
    env["COLAB_GPU"] = "1"
    env["UVICORN_PORT"] = "8889" # 使用一個新的埠號

    # 執行部署腳本
    # 這次我們執行完整的 run.sh，因為我們也想驗證 FastAPI 能否啟動
    process = subprocess.Popen(
        ["bash", str(project_dir / "run.sh")],
        cwd=project_dir, # 這次我們直接從專案目錄執行，因為 run.sh 內部會 cd
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        env=env
    )

    # 讀取並打印即時輸出，同時進行檢查
    output_lines = []
    venv_created = False
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
    for line in iter(process.stdout.readline, ''):
        clean_line = ansi_escape.sub('', line).strip()
        print(clean_line)
        output_lines.append(clean_line)
        if "Creating virtualenv" in clean_line or "Using virtualenv" in clean_line:
            venv_created = True

    process.stdout.close()
    return_code = process.wait()

    full_output = "".join(output_lines)

    # 斷言
    assert venv_created is False, "Poetry 不應該在 Colab 模式下建立虛擬環境"
    assert any("==> [Phase: Environment Sensing] 環境變數 POETRY_VIRTUALENVS_CREATE 已設定為 false。" in line for line in output_lines), "日誌中應包含設定環境變數的訊息"
    assert any("==> [Phase: Mission Complete] 後端服務已成功啟動並通過健康檢查！" in line for line in output_lines), "日誌中應包含任務完成的訊息"
    assert return_code == 0, f"部署腳本執行失敗，返回碼: {return_code}"
