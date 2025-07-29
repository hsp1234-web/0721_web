# -*- coding: utf-8 -*-
import queue
log_queue = queue.Queue(maxsize=100)
def add_log(message: str):
    try:
        log_queue.put_nowait(message)
    except queue.Full:
        pass
def get_log() -> str:
    return log_queue.get()
