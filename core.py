import subprocess
import time
import sys
import os
import psutil
from multiprocessing import Process, Queue, Event
from logger.main import logger_process

# --- 全域設定 ---
# 將專案根目錄加入 Python 路徑，這樣才能找到 logger, main, run 等模組
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def system_monitoring_process(log_queue: Queue, stop_event: Event):
    """
    一個獨立的進程，負責定期收集系統狀態並放入日誌佇列。
    """
    print("[監控進程] 啟動。")

    # 獲取當前進程的磁碟分區
    try:
        disk_partition = psutil.disk_partitions()[0].mountpoint
    except IndexError:
        print("[監控進程] 警告: 無法找到磁碟分區，將無法記錄磁碟使用情況。")
        disk_partition = None

    while not stop_event.is_set():
        try:
            # 收集 CPU 和記憶體使用情況
            cpu_usage = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()

            # 收集磁碟使用情況
            disk_usage = psutil.disk_usage(disk_partition).percent if disk_partition else -1.0

            # 準備數據
            monitor_data = {
                "type": "monitor",
                "data": (
                    time.strftime('%Y-%m-%d %H:%M:%S'),
                    cpu_usage,
                    memory_info.percent,
                    disk_usage
                )
            }

            # 放入佇列
            log_queue.put(monitor_data)

            # 每 10 秒收集一次
            time.sleep(10)
        except Exception as e:
            print(f"[監控進程] 發生錯誤: {e}")
            time.sleep(10) # 發生錯誤時也等待，避免快速失敗循環

    print("[監控進程] 收到停止信號，正在關閉。")


def main():
    """
    核心指揮官主函數。
    """
    print("[核心指揮官] 系統啟動...")

    # 1. 建立通訊佇列和停止事件
    log_queue = Queue()
    stop_event = Event()

    processes = []

    try:
        # 2. 啟動日誌寫入進程
        log_process = Process(target=logger_process, args=(log_queue, stop_event))
        log_process.start()
        processes.append(log_process)
        print("[核心指揮官] 日誌進程已啟動。")

        # 3. 啟動系統監控進程
        monitor_process = Process(target=system_monitoring_process, args=(log_queue, stop_event))
        monitor_process.start()
        processes.append(monitor_process)
        print("[核心指揮官] 系統監控進程已啟動。")

        # 4. 啟動 Web 伺服器子進程
        # 注意：我們直接用 python 執行 run.py，而不是透過 shell
        web_server_command = [sys.executable, "run.py", "--host", "0.0.0.0", "--port", "8000"]
        web_server_process = subprocess.Popen(web_server_command)
        processes.append(web_server_process)
        print(f"[核心指揮官] Web 伺服器進程已啟動 (PID: {web_server_process.pid})。")

        # 模擬一個簡單的日誌發送
        log_queue.put({
            "type": "log",
            "data": (time.strftime('%Y-%m-%d %H:%M:%S'), "INFO", "core", "核心系統已成功啟動所有進程。")
        })

        # 5. 監控與等待
        print("[核心指揮官] 系統運行中... 按下 Ctrl+C 來停止。")
        while True:
            # 檢查 Web 伺服器是否意外退出
            if web_server_process.poll() is not None:
                print("[核心指揮官] 偵測到 Web 伺服器進程已終止，正在關閉整個系統...")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[核心指揮官] 收到使用者中斷信號 (Ctrl+C)，正在優雅關閉所有進程...")
    except Exception as e:
        print(f"\n[核心指揮官] 發生未預期錯誤: {e}，正在關閉系統...")
    finally:
        # --- 優雅關閉 ---
        print("[核心指揮官] 開始關閉程序...")

        # 1. 通知所有基於 Event 的進程停止
        stop_event.set()

        # 2. 溫柔地終止 Web 伺服器
        if isinstance(processes[-1], subprocess.Popen) and processes[-1].poll() is None:
            print("[核心指揮官] 正在終止 Web 伺服器...")
            processes[-1].terminate() # 發送 SIGTERM
            try:
                processes[-1].wait(timeout=10) # 等待最多 10 秒
            except subprocess.TimeoutExpired:
                print("[核心指揮官] Web 伺服器終止超時，強制終止 (kill)。")
                processes[-1].kill()

        # 3. 等待日誌和監控進程結束
        # 將 None 作為哨兵值放入佇列，通知日誌進程處理完畢後退出
        log_queue.put(None)

        for p in processes[:-1]: # 除了 web server process
            if isinstance(p, Process):
                print(f"[核心指揮官] 等待 {p.name} 結束...")
                p.join(timeout=5) # 等待最多 5 秒
                if p.is_alive():
                    print(f"[核心指揮官] {p.name} 關閉超時，強制終止。")
                    p.terminate()

        print("[核心指揮官] 所有進程已關閉。系統結束。")
        log_queue.close()
        log_queue.join_thread()

if __name__ == "__main__":
    main()
