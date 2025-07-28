# -*- coding: utf-8 -*-
"""
中央任務佇列

提供一個全域單例的 multiprocessing.Queue，用於在調度器和工作者之間傳遞任務。
"""

from multiprocessing import Queue

# 全域單例的任務佇列
task_queue = Queue()
