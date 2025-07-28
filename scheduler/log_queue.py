# -*- coding: utf-8 -*-
"""
中央日誌佇列

提供一個全域單例的 multiprocessing.Queue，用於從所有進程收集日誌、
效能指標和錯誤報告，並由一個專門的寫入器寫入資料庫。
"""

from multiprocessing import Queue

# 全域單例的日誌佇列
log_queue = Queue()
