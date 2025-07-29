# -*- coding: utf-8 -*-
"""
共享日誌佇列模組

這個模組提供一個全域的、線程安全的佇列，用於在系統的不同部分之間傳遞日誌訊息。
- launch.py 作為日誌的生產者 (Producer)，將啟動過程中的日誌放入佇列。
- apps/monitor/main.py 作為日誌的消費者 (Consumer)，從佇列中讀取日誌並透過 SSE 推送給前端。
"""
import queue

# 建立一個全域的佇列實例
# maxsize=100 可以防止在沒有消費者時，佇列無限增長導致記憶體耗盡
log_queue = queue.Queue(maxsize=100)

def add_log(message: str):
    """
    向日誌佇列中添加一條新訊息。
    如果佇列已滿，將會阻塞，直到有空間為止。
    為了避免阻塞，我們使用 put_nowait，並在佇列滿時忽略該條日誌。
    """
    try:
        log_queue.put_nowait(message)
    except queue.Full:
        # 在高併發情況下，如果消費者處理不過來，我們可以選擇丟棄一些日誌
        print(f"警告：共享日誌佇列已滿，日誌訊息被丟棄: {message}")
        pass

def get_log() -> str:
    """
    從日誌佇列中獲取一條訊息。
    如果佇列為空，將會阻塞等待，直到有新訊息為止。
    """
    return log_queue.get()
