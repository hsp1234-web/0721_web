import os
import sys
import time
from multiprocessing import Event, Queue
from unittest.mock import MagicMock

import pytest

# 將專案根目錄加入 sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logger import main as logger_main


@pytest.fixture
def mock_duckdb(monkeypatch):
    """替換 duckdb.connect，使其返回一個 mock connection。"""
    mock_conn = MagicMock()
    mock_connect = MagicMock(return_value=mock_conn)
    monkeypatch.setattr(logger_main.duckdb, "connect", mock_connect)
    return mock_connect, mock_conn


@pytest.fixture
def mock_pandas(monkeypatch):
    """替換 pandas.DataFrame，使其返回一個 mock DataFrame。"""
    mock_df = MagicMock()
    mock_dataframe_constructor = MagicMock(return_value=mock_df)
    monkeypatch.setattr(logger_main.pd, "DataFrame", mock_dataframe_constructor)
    return mock_dataframe_constructor


def test_logger_process_writes_on_batch_size(mock_duckdb, mock_pandas):
    """測試當達到 BATCH_SIZE 時，是否觸發寫入資料庫。"""
    log_queue = Queue()
    stop_event = Event()

    # 讓 BATCH_SIZE 變小以便測試
    logger_main.BATCH_SIZE = 3

    # 放入 3 個日誌項
    for i in range(3):
        log_queue.put({"type": "log", "data": (f"ts_{i}", "INFO", "test", f"msg_{i}")})

    # 放入一個 None 來立即停止進程
    log_queue.put(None)

    # 執行 logger_process
    logger_main.logger_process(log_queue, stop_event)

    # 驗證:
    # 1. pd.DataFrame 是否被以正確的數據呼叫
    mock_pandas.assert_called_once()
    # 2. duckdb connection 的 execute 是否被呼叫
    _mock_connect, mock_conn = mock_duckdb
    assert mock_conn.execute.call_count > 0


def test_logger_process_writes_on_timeout(mock_duckdb, mock_pandas):
    """測試當超時後，是否觸發寫入資料庫。"""
    log_queue = Queue()
    stop_event = Event()

    # 設定超時時間
    logger_main.BATCH_TIMEOUT = 1
    logger_main.BATCH_SIZE = 10  # 確保不會因為數量滿而觸發

    # 放入 1 個日誌項
    log_queue.put({"type": "log", "data": ("ts_1", "INFO", "test", "msg_1")})

    # 模擬時間流逝超過 timeout
    original_time = time.time
    # 第一次 time.time() 回傳現在，之後的呼叫都回傳 2 秒後
    side_effect = [original_time(), original_time() + 2]
    time.time = MagicMock(side_effect=side_effect)

    # 放入 None 來停止
    log_queue.put(None)

    logger_main.logger_process(log_queue, stop_event)

    # 驗證:
    _mock_connect, mock_conn = mock_duckdb
    assert mock_conn.execute.call_count > 0

    # 還原 time.time
    time.time = original_time


def test_logger_process_writes_remaining_on_stop(mock_duckdb, mock_pandas):
    """測試當收到停止信號 (None) 時，是否會寫入剩餘的日誌。"""
    log_queue = Queue()
    stop_event = Event()

    logger_main.BATCH_SIZE = 10

    # 放入少於 BATCH_SIZE 的日誌
    log_queue.put({"type": "log", "data": ("ts_1", "INFO", "test", "msg_1")})
    log_queue.put({"type": "monitor", "data": ("ts_2", 1.0, 2.0, 3.0)})

    # 發送停止信號
    log_queue.put(None)

    logger_main.logger_process(log_queue, stop_event)

    # 驗證:
    # pd.DataFrame 應該被呼叫了兩次（一次日誌，一次監控）
    assert mock_pandas.call_count == 2
    # duckdb execute 應該也被呼叫了
    _mock_connect, mock_conn = mock_duckdb
    assert mock_conn.execute.call_count > 0
