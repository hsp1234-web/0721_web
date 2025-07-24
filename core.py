import argparse
import os
import subprocess  # nosec B404
import sys
import time
from multiprocessing import Process, Queue
from multiprocessing.synchronize import Event
from typing import Any, Dict, List

import psutil

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from logger.main import logger_process  # noqa: E402


def system_monitoring_process(
    log_queue: "Queue[Dict[str, Any]]", stop_event: Event
) -> None:
    """一個獨立的進程，負責定期收集系統狀態並放入日誌佇列。"""
    print("[監控進程] 啟動。")
    try:
        disk_partition = psutil.disk_partitions()[0].mountpoint
    except IndexError:
        print("[監控進程] 警告: 無法找到磁碟分區，將無法記錄磁碟使用情況。")
        disk_partition = None

    while not stop_event.is_set():
        try:
            cpu_usage = psutil.cpu_percent(interval=None)
            memory_info = psutil.virtual_memory()
            disk_usage = (
                psutil.disk_usage(disk_partition).percent if disk_partition else -1.0
            )
            monitor_data = {
                "type": "monitor",
                "data": (
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    cpu_usage,
                    memory_info.percent,
                    disk_usage,
                ),
            }
            log_queue.put(monitor_data)
            time.sleep(10)
        except Exception as e:
            print(f"[監控進程] 發生錯誤: {e}")
            time.sleep(10)

    print("[監控進程] 收到停止信號，正在關閉。")


def main() -> None:
    """核心指揮官主函數。"""
    parser = argparse.ArgumentParser(description="核心進程指揮官")
    parser.add_argument(
        "--host", type=str, default="0.0.0.0", help="Web 伺服器綁定的主機"
    )
    parser.add_argument("--port", type=int, default=8000, help="Web 伺服器監聽的埠號")
    parser.add_argument("--reload", action="store_true", help="為 Web 伺服器啟用熱重載")
    args = parser.parse_args()

    print("[核心指揮官] 系統啟動...")
    print(
        f"[核心指揮官] Web 伺服器設定 -> "
        f"Host: {args.host}, Port: {args.port}, Reload: {args.reload}"
    )

    log_queue: "Queue[Any]" = Queue()
    stop_event = Event()
    processes: List[Any] = []

    try:
        log_process = Process(target=logger_process, args=(log_queue, stop_event))
        log_process.start()
        processes.append(log_process)
        print("[核心指揮官] 日誌進程已啟動。")

        monitor_process = Process(
            target=system_monitoring_process, args=(log_queue, stop_event)
        )
        monitor_process.start()
        processes.append(monitor_process)
        print("[核心指揮官] 系統監控進程已啟動。")

        web_server_command = [
            sys.executable,
            "run.py",
            "--host",
            args.host,
            "--port",
            str(args.port),
        ]
        if args.reload:
            web_server_command.append("--reload")

        web_server_process = subprocess.Popen(web_server_command)  # nosec B603
        processes.append(web_server_process)
        print(f"[核心指揮官] Web 伺服器進程已啟動 (PID: {web_server_process.pid})。")

        log_queue.put(
            {
                "type": "log",
                "data": (
                    time.strftime("%Y-%m-%d %H:%M:%S"),
                    "INFO",
                    "core",
                    "核心系統已成功啟動所有進程。",
                ),
            }
        )

        print("[核心指揮官] 系統運行中... 按下 Ctrl+C 來停止。")
        while True:
            if web_server_process.poll() is not None:
                print("[核心指揮官] 偵測到 Web 伺服器進程已終止，正在關閉整個系統...")
                break
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n[核心指揮官] 收到使用者中斷信號 (Ctrl+C)，正在優雅關閉所有進程...")
    except Exception as e:
        print(f"\n[核心指揮官] 發生未預期錯誤: {e}，正在關閉系統...")
    finally:
        print("[核心指揮官] 開始關閉程序...")
        stop_event.set()

        server_proc = processes[-1]
        if isinstance(server_proc, subprocess.Popen) and server_proc.poll() is None:
            print("[核心指揮官] 正在終止 Web 伺服器...")
            server_proc.terminate()
            try:
                server_proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                print("[核心指揮官] Web 伺服器終止超時，強制終止 (kill)。")
                server_proc.kill()

        log_queue.put(None)

        for p in processes[:-1]:
            if isinstance(p, Process):
                print(f"[核心指揮官] 等待 {p.name} 結束...")
                p.join(timeout=5)
                if p.is_alive():
                    print(f"[核心指揮官] {p.name} 關閉超時，強制終止。")
                    p.terminate()

        print("[核心指揮官] 所有進程已關閉。系統結束。")
        log_queue.close()
        log_queue.join_thread()


if __name__ == "__main__":
    main()
