import asyncio
import psutil
import time
from core.config import settings

class PerformanceMonitor:
    def __init__(self, manager):
        self.manager = manager
        self.is_running = False

    async def run(self):
        self.is_running = True
        while self.is_running:
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().used

            await self.manager.broadcast({
                "event_type": "PERFORMANCE_UPDATE",
                "payload": {
                    "cpu_usage": cpu_usage,
                    "ram_usage": ram_usage,
                    "timestamp": time.time()
                }
            })
            await asyncio.sleep(settings.STATUS_REFRESH_INTERVAL)

    def stop(self):
        self.is_running = False
