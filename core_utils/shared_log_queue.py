# -*- coding: utf-8 -*-
import queue
log_queue = queue.Queue(maxsize=100)
def add_log(message: str):
    try:
        log_queue.put_nowait(message)
    except queue.Full:
        pass
def get_log() -> str:
    # 使用 timeout 避免永久阻塞，便於後端服務優雅地關閉
    try:
        return log_queue.get(timeout=1)
    except queue.Empty:
        return None

def get_all_logs() -> list[str]:
    """
    非阻塞地獲取當前佇列中的所有日誌。
    """
    return list(log_queue.queue)
