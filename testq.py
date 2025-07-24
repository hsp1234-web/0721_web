#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
testq.py - 快速測試啟動器

此腳本只運行核心的功能性測試 (位於 tests/ 目錄下)，
忽略程式碼風格、型別檢查等，用於在開發過程中快速驗證功能是否正常。
"""

import sys

import pytest

if __name__ == "__main__":
    print("🚀 執行快速功能測試 (Quick Test)...")
    # 只運行 tests/ 目錄下的測試
    # 返回 pytest 的退出碼
    sys.exit(pytest.main(["tests/"]))
