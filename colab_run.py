import atexit
import subprocess  # nosec B404
import sys
import time
from typing import Any, Optional

# --- 全域狀態 ---
_backend_process: Optional[subprocess.Popen[Any]] = None
_start_time: Optional[float] = None


def _cleanup_on_exit() -> None:
    """使用 atexit 註冊一個清理函數，確保在 Colab 執行緒退出時能終止後端。"""
    print("偵測到執行環境退出，正在自動清理後端進程...")
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
        print(f"後端系統似乎已經在運行 (PID: {_backend_process.pid})。請先執行 stop_backend()。")
        return

    print(f"正在啟動後端核心服務 (run.py) on port {port}...")

    try:
        # 使用 run.py 作為新的啟動入口
        command = [sys.executable, "run.py", "--port", str(port)]
        if reload:
            command.append("--reload")

        # 我們不再需要捕獲 stdout/stderr，因為日誌會透過 WebSocket 傳輸
        _backend_process = subprocess.Popen(command)  # nosec B603

        _start_time = time.time()
        time.sleep(5)  # 等待伺服器啟動

        if _backend_process.poll() is None:
            print(f"後端系統已成功啟動。PID: {_backend_process.pid}")
        else:
            print("後端啟動失敗！請檢查終端機輸出。")
            _backend_process = None

    except Exception as e:
        print(f"執行 start_backend 時發生未知錯誤: {e}")
        _backend_process = None


def stop_backend() -> None:
    """停止正在運行的後端系統。"""
    global _backend_process

    if _backend_process is None or _backend_process.poll() is not None:
        print("後端系統未在運行。")
        return

    print(f"正在發送終止信號給後端進程 (PID: {_backend_process.pid})...")
    _backend_process.terminate()
    try:
        _backend_process.wait(timeout=10)
        print("後端進程已成功關閉。")
    except subprocess.TimeoutExpired:
        print("後端進程關閉超時，正在強制終止 (kill)...")
        _backend_process.kill()
        print("後端進程已被強制終止。")

    _backend_process = None


# 移除 get_backend_logs，因為日誌現在透過 WebSocket 處理
