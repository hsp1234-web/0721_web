# apps/transcriber/transcriber_worker.py
import time
import random
import multiprocessing as mp

def run_transcription_worker_process(task_queue: mp.Queue, result_queue: mp.Queue, task_store: dict, result_store: dict):
    """
    這是在一個獨立進程中運行的轉錄工作者函式。
    它會從任務佇列中獲取任務，模擬轉錄，然後將結果放入結果佇列和共享字典。
    """
    print("轉錄工作者進程已啟動。")

    while True:
        try:
            # 從隊列中獲取任務，這是一個阻塞操作
            task = task_queue.get()

            # None 是一個信號，表示該停止了
            if task is None:
                print("工作者收到停止信號，正在關閉。")
                break

            task_id = task.get("task_id", "unknown_task")
            file_path = task.get("file_path", "unknown_file")

            print(f"工作者正在處理任務: {task_id}，檔案: {file_path}")

            # 更新共享儲存中的狀態為 "processing"
            if task_id in task_store:
                # 注意：直接修改 multiprocessing.Manager().dict() 的子項目可能不會觸發同步
                # 最可靠的方式是替換整個物件
                current_task_info = task_store[task_id]
                current_task_info['status'] = 'processing'
                task_store[task_id] = current_task_info

            # --- 模擬轉錄過程 ---
            # 模擬 1 到 3 秒的隨機處理時間
            processing_time = random.uniform(1, 3)
            time.sleep(processing_time)
            # 為了通過 e2e 測試，我們返回一個固定的、非空的字串
            transcribed_text = "這是一個模擬的轉錄結果。"
            # --- 模擬結束 ---

            result = {
                "task_id": task_id,
                "status": "completed",
                "result_text": transcribed_text,
                "file_path": file_path
            }

            # 將結果放入結果佇列，並更新共享的結果儲存
            result_queue.put(result)
            result_store[task_id] = result

            print(f"工作者完成任務: {task_id}")

        except Exception as e:
            # 在實際應用中，這裡應該有更健壯的錯誤日誌
            print(f"工作者發生錯誤: {e}")
            # 考慮加入一個錯誤恢復機制或將任務標記為失敗
            if 'task_id' in locals():
                error_result = {
                    "task_id": task_id,
                    "status": "failed",
                    "error_message": str(e)
                }
                result_store[task_id] = error_result
