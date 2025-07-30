# -*- coding: utf-8 -*-
"""
核心工具：資源監控器 (Resource Monitor)

當作為獨立腳本執行時，此工具會定期收集系統資源使用情況，
並以標準化的 JSON 格式將其輸出到 stdout。
"""
import time
import json
import psutil

def log(level, service, message, **kwargs):
    """標準化的 JSON 日誌輸出"""
    log_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "level": level,
        "service": service,
        "message": message,
        **kwargs
    }
    print(json.dumps(log_entry, ensure_ascii=False))

def monitor(interval_seconds: int = 5):
    """
    以指定的間隔，持續監控並記錄系統資源。

    Args:
        interval_seconds: 監控的時間間隔（秒）。
    """
    log("INFO", "resource_monitor", "資源監控服務已啟動", interval=interval_seconds)

    while True:
        try:
            # 獲取 CPU 使用率
            cpu_usage = psutil.cpu_percent(interval=None) #瞬時值

            # 獲取記憶體使用情況
            memory = psutil.virtual_memory()
            ram_usage_percent = memory.percent

            # 獲取磁碟 I/O
            disk_io = psutil.disk_io_counters()

            # 獲取網路 I/O
            net_io = psutil.net_io_counters()

            log(
                "DEBUG",
                "resource_monitor",
                "performance_update",
                cpu_percent=cpu_usage,
                ram_percent=ram_usage_percent,
                disk_read_mb=round(disk_io.read_bytes / (1024**2), 2),
                disk_write_mb=round(disk_io.write_bytes / (1024**2), 2),
                net_sent_mb=round(net_io.bytes_sent / (1024**2), 2),
                net_recv_mb=round(net_io.bytes_recv / (1024**2), 2)
            )

            time.sleep(interval_seconds)

        except KeyboardInterrupt:
            log("INFO", "resource_monitor", "收到中斷訊號，資源監控服務正在關閉。")
            break
        except Exception as e:
            log("ERROR", "resource_monitor", f"監控迴圈發生錯誤: {e}")
            time.sleep(interval_seconds * 2) # 發生錯誤時，延長等待時間

if __name__ == "__main__":
    # 允許從命令列傳入監控間隔，預設為 5 秒
    import sys
    interval = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    monitor(interval)
