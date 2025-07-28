# -*- coding: utf-8 -*-
"""
智慧任務調度服務主啟動器
"""

import argparse
import time
import sys
from scheduler.core_scheduler import Scheduler
from scheduler.reporting import generate_summary_report, generate_performance_report
from scheduler.task_queue import task_queue

def main():
    """
    主函式，解析命令列參數並啟動調度器。
    """
    parser = argparse.ArgumentParser(description="智慧任務調度服務")
    parser.add_argument(
        '--dev-mode',
        action='store_true',
        help='啟用開發者模式，執行一組預定義的測試任務並在完成後自動關閉。'
    )
    parser.add_argument(
        '--db-path',
        type=str,
        default='scheduler.db',
        help='指定資料庫檔案的路徑。'
    )
    args = parser.parse_args()

    scheduler = Scheduler(db_path=args.db_path)

    try:
        scheduler.start()

        if args.dev_mode:
            print("[Main] 開發者模式已啟用。")
            run_dev_mode(scheduler)
        else:
            print("[Main] 服務已啟動，按 Ctrl+C 關閉。")
            # 在正常模式下，主執行緒可以保持運行或執行其他監控任務
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n[Main] 偵測到手動中斷...")
    except Exception as e:
        print(f"[Main] 發生未預期的錯誤: {e}", file=sys.stderr)
    finally:
        scheduler.shutdown()

def run_dev_mode(scheduler):
    """
    執行開發者模式的特定邏輯。
    """
    print("[DevMode] 正在添加測試任務...")
    tasks = [
        {'action': 'success_test', 'name': 'Dev-Success-1', 'duration': 1},
        {'action': 'success_test', 'name': 'Dev-Success-2', 'duration': 2},
        {'action': 'failure_test', 'name': 'Dev-Failure-1'},
        {'action': 'failure_test', 'name': 'Dev-Failure-2'},
        {'action': 'unexpected_error', 'name': 'Dev-Unknown-1'}
    ]
    for task in tasks:
        scheduler.add_task(task)

    print("[DevMode] 所有任務已添加。等待任務完成...")

    # 等待所有任務被取出並處理
    # 這是一個簡化的等待邏輯
    while not task_queue.empty():
        time.sleep(1)

    # 再多等待幾秒，確保最後的任務有時間被處理和寫入資料庫
    print("[DevMode] 佇列已空，額外等待 3 秒以完成日誌寫入...")
    time.sleep(3)

    print("[DevMode] 任務執行完畢。正在生成報告...")
    generate_summary_report(scheduler.db_path)
    generate_performance_report(scheduler.db_path)

if __name__ == "__main__":
    main()
