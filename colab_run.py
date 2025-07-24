import atexit
import subprocess  # nosec B404
import sys
import time
from typing import Any, Optional

from colab_display import display_error, display_log_message, display_system_status

# --- 全域狀態 ---
_backend_process: Optional[subprocess.Popen[Any]] = None
_start_time: Optional[float] = None


def _cleanup_on_exit() -> None:
    """使用 atexit 註冊一個清理函數，確保在 Colab 執行緒退出時能終止後端。"""
    display_log_message("偵測到執行環境退出，正在自動清理後端進程...")
    stop_backend()


atexit.register(_cleanup_on_exit)


def start_backend(port: int = 8000, reload: bool = False) -> None:
    """在 Colab 環境中啟動後端系統。

    Args:
    ----
        port: Web 伺服器要監聽的埠號。
        reload: 是否啟用熱重載 (僅供開發)。

    """
    global _backend_process, _start_time

    if _backend_process and _backend_process.poll() is None:
        display_error("後端系統似乎已經在運行。請先執行 stop_backend()。")
        display_system_status(
            {
                "status": "RUNNING",
                "pid": _backend_process.pid,
                "start_time": _start_time,
                "message": "系統已在運行中，無需重複啟動。",
            }
        )
        return

    display_system_status(
        {"status": "STARTING", "message": "正在啟動後端核心服務 (core.py)..."}
    )

    try:
        command = [sys.executable, "core.py", "--port", str(port)]
        if reload:
            command.append("--reload")

        _backend_process = subprocess.Popen(  # nosec B603
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )
        _start_time = time.time()
        time.sleep(3)

        if _backend_process.poll() is None:
            display_system_status(
                {
                    "status": "RUNNING",
                    "pid": _backend_process.pid,
                    "start_time": _start_time,
                    "message": f"後端系統已在埠號 {port} 上成功啟動。",
                }
            )
        else:
            stdout, stderr = _backend_process.communicate()
            error_message = f"後端啟動失敗！\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
            display_error(error_message)
            _backend_process = None

    except Exception as e:
        display_error(f"執行 start_backend 時發生未知錯誤: {e}")
        _backend_process = None


def stop_backend() -> None:
    """停止正在運行的後端系統。"""
    global _backend_process

    if _backend_process is None or _backend_process.poll() is not None:
        display_system_status({"status": "STOPPED", "message": "後端系統未在運行。"})
        return

    display_log_message(f"正在發送終止信號給後端進程 (PID: {_backend_process.pid})...")
    _backend_process.terminate()
    try:
        _backend_process.wait(timeout=15)
        display_log_message("後端進程已成功關閉。")
    except subprocess.TimeoutExpired:
        display_log_message("後端進程關閉超時，正在強制終止 (kill)...")
        _backend_process.kill()
        display_log_message("後端進程已被強制終止。")

    _backend_process = None
    display_system_status({"status": "STOPPED", "message": "系統已成功停止。"})


def get_backend_logs() -> None:
    """獲取後端進程的即時日誌（如果有的話）。

    這是一個簡化的實現，只適用於 stdout/stderr。
    """
    if _backend_process and _backend_process.poll() is None:
        try:
            # 非阻塞讀取，但可能不適用所有情況
            if _backend_process.stdout:
                stdout = _backend_process.stdout.read()
                if stdout:
                    display_log_message("--- STDOUT ---")
                    print(stdout)
            if _backend_process.stderr:
                stderr = _backend_process.stderr.read()
                if stderr:
                    display_log_message("--- STDERR ---")
                    print(stderr)
        except Exception as e:
            display_error(f"讀取日誌時出錯: {e}")
    else:
        display_error("後端未運行，無法獲取日誌。")
