# -*- coding: utf-8 -*-
import datetime
from collections import deque

class ColabLogManager:
    def __init__(self, max_logs=15):
        self.logs = deque(maxlen=max_logs)

    def log(self, message, level="INFO"):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] [{level}] {message}")

    def get_recent_logs(self, num_logs=None):
        if num_logs:
            # 返回列表的最後N個元素
            return list(self.logs)[-num_logs:]
        return list(self.logs)
