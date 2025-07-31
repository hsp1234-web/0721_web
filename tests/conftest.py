# -*- coding: utf-8 -*-
import pytest
import json
from pathlib import Path

LAUNCH_CONFIG_PATH = Path("config.json")

@pytest.fixture(scope="module")
def full_mode_config():
    """
    一個模組範圍的 Pytest fixture，用於建立觸發完整模式的 config.json。
    此 fixture 會在測試執行前建立檔案，並在測試結束後自動清理。
    """
    # 儲存可能已存在的原始設定檔
    original_content = None
    if LAUNCH_CONFIG_PATH.exists():
        with open(LAUNCH_CONFIG_PATH, "r", encoding="utf-8") as f:
            original_content = f.read()

    # 寫入測試用的設定
    config_data = {"FAST_TEST_MODE": False}
    with open(LAUNCH_CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config_data, f)

    yield

    # 測試結束後清理
    if original_content:
        # 如果原始檔案存在，則恢復它
        with open(LAUNCH_CONFIG_PATH, "w", encoding="utf-8") as f:
            f.write(original_content)
    else:
        # 如果原始檔案不存在，則刪除我們建立的檔案
        if LAUNCH_CONFIG_PATH.exists():
            LAUNCH_CONFIG_PATH.unlink()
