# apps/transcriber/queues.py
import multiprocessing

# 使用 multiprocessing.Queue 來在主進程和背景工作者之間傳遞任務
_task_queue = multiprocessing.Queue()
_result_queue = multiprocessing.Queue()

def get_task_queue():
    """返回單例的任務佇列。"""
    return _task_queue

def get_result_queue():
    """返回單例的結果佇列。"""
    return _result_queue

def get_task_store(manager):
    """返回由 Manager 管理的共享任務字典。"""
    return manager.dict()

def get_result_store(manager):
    """返回由 Manager 管理的共享結果字典。"""
    return manager.dict()
