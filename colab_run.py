import subprocess
import sys
import os
import time
import atexit
from colab_display import display_system_status, display_error, display_log_message

# --- 全域狀態 ---
# 使用一個簡單的字典來追蹤後端進程的狀態
# 在真實的多使用者或複雜場景下，可能需要更健壯的狀態管理器
_backend_process = None
_start_time = None

def _cleanup_on_exit():
    """
    使用 atexit 註冊一個清理函數，確保在 Colab 執行緒退出時，後端進程也能被終止。
    """
    display_log_message("偵測到執行環境退出，正在自動清理後端進程...")
    stop_backend()

# 註冊清理函數
atexit.register(_cleanup_on_exit)


def start_backend(port: int = 8000, reload: bool = False):
    """
    在 Colab 環境中啟動後端系統。

    Args:
        port (int): Web 伺服器要監聽的埠號。
        reload (bool): 是否啟用熱重載 (僅供開發)。
    """
    global _backend_process, _start_time

    if _backend_process and _backend_process.poll() is None:
        display_error("後端系統似乎已經在運行。請先執行 stop_backend()。")
        display_system_status({
            'status': 'RUNNING',
            'pid': _backend_process.pid,
            'start_time': _start_time,
            'message': '系統已在運行中，無需重複啟動。'
        })
        return

    display_system_status({
        'status': 'STARTING',
        'message': '正在啟動後端核心服務 (core.py)...'
    })

    try:
        # 準備命令
        # 注意：我們傳遞了額外的參數給 core.py，以便它知道如何啟動 run.py
        # 這是一個簡單的實現，未來可以透過更複雜的配置管理來優化
        command = [
            sys.executable,
            "core.py",
            "--port", str(port),
        ]
        if reload:
            command.append("--reload")

        # 在一個新的子進程中啟動 core.py
        # Popen 不會阻塞，這使得 Colab Cell 可以繼續執行
        _backend_process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True, # 將輸出解碼為文字
            bufsize=1, # 行緩衝
        )

        _start_time = time.time()

        # 等待一小段時間，讓進程有時間啟動或失敗
        time.sleep(3)

        if _backend_process.poll() is None:
            # 如果進程仍在運行，說明啟動成功
            display_system_status({
                'status': 'RUNNING',
                'pid': _backend_process.pid,
                'start_time': _start_time,
                'message': f'後端系統已在埠號 {port} 上成功啟動。'
            })
        else:
            # 如果進程已經退出，說明啟動失敗
            stdout, stderr = _backend_process.communicate()
            error_message = f"後端啟動失敗！\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            display_error(error_message)
            _backend_process = None

    except Exception as e:
        display_error(f"執行 start_backend 時發生未知錯誤: {e}")
        _backend_process = None

def stop_backend():
    """
    停止正在運行的後端系統。
    """
    global _backend_process

    if _backend_process is None or _backend_process.poll() is not None:
        display_system_status({
            'status': 'STOPPED',
            'message': '後端系統未在運行。'
        })
        return

    display_log_message(f"正在發送終止信號給後端進程 (PID: {_backend_process.pid})...")

    # core.py 中有優雅關閉的邏輯，所以我們首先嘗試 terminate (SIGTERM)
    _backend_process.terminate()

    try:
        # 等待最多 15 秒讓它優雅關閉
        _backend_process.wait(timeout=15)
        display_log_message("後端進程已成功關閉。")
    except subprocess.TimeoutExpired:
        display_log_message("後端進程關閉超時，正在強制終止 (kill)...")
        _backend_process.kill()
        display_log_message("後端進程已被強制終止。")

    _backend_process = None
    display_system_status({
        'status': 'STOPPED',
        'message': '系統已成功停止。'
    })

def get_backend_logs():
    """
    獲取後端進程的即時日誌（如果有的話）。
    這是一個簡化的實現，只適用於 stdout/stderr。
    """
    if _backend_process and _backend_process.poll() is None:
        try:
            # 這是非阻塞讀取，但可能不適用所有情況
            # 一個更健壯的實現會使用 select 或執行緒
            stdout = _backend_process.stdout.read()
            stderr = _backend_process.stderr.read()
            if stdout:
                display_log_message("--- STDOUT ---")
                print(stdout)
            if stderr:
                display_log_message("--- STDERR ---")
                print(stderr)
        except Exception as e:
            display_error(f"讀取日誌時出錯: {e}")
    else:
        display_error("後端未運行，無法獲取日誌。")
