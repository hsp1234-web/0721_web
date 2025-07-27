# launcher/src/core/process_manager.py

import subprocess
import sys
import threading
from pathlib import Path

from ..display.dashboard import Dashboard

class ProcessManager:
    """負責啟動和管理子程序，例如 FastAPI 伺服器。"""

    def __init__(self, dashboard: Dashboard, project_path: Path):
        self.dashboard = dashboard
        self.project_path = project_path
        self.server_process = None

    def _stream_output(self, pipe, log_level: str):
        """從子程序的輸出流中讀取並記錄日誌。"""
        try:
            for line in iter(pipe.readline, ''):
                self.dashboard.add_log(f"[{log_level}] {line.strip()}")
            pipe.close()
        except Exception as e:
            self.dashboard.add_log(f"[bold red]讀取日誌流時出錯: {e}[/bold red]")

    def start_server(self, main_app_file: str = "main_api.py", env: dict = None):
        """在一個單獨的執行緒中啟動 FastAPI 伺服器。"""
        command = [sys.executable, main_app_file]

        self.dashboard.add_log(f"正在執行命令: {' '.join(command)}")

        try:
            self.server_process = subprocess.Popen(
                command,
                cwd=self.project_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env
            )

            self.dashboard.add_log(f"✅ 主應用程式程序已啟動 (PID: {self.server_process.pid})。")

            # 為 stdout 和 stderr 建立單獨的執行緒來處理輸出
            stdout_thread = threading.Thread(
                target=self._stream_output,
                args=(self.server_process.stdout, "SERVER"),
                daemon=True,
            )
            stderr_thread = threading.Thread(
                target=self._stream_output,
                args=(self.server_process.stderr, "ERROR"),
                daemon=True,
            )

            stdout_thread.start()
            stderr_thread.start()

        except FileNotFoundError:
            self.dashboard.add_log(
                f"[bold red]❌ 錯誤: 找不到主應用程式檔案 '{main_app_file}'。[/bold red]"
            )
        except Exception as e:
            self.dashboard.add_log(
                f"[bold red]❌ 啟動主應用程式時發生嚴重錯誤: {e}[/bold red]"
            )

    def stop_server(self):
        """停止 FastAPI 伺服器。"""
        if self.server_process and self.server_process.poll() is None:
            self.dashboard.add_log("正在優雅地終止主應用程式...")
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=10)
                self.dashboard.add_log("主應用程式已成功終止。")
            except subprocess.TimeoutExpired:
                self.dashboard.add_log(
                    "[bold yellow]警告: 主應用程式終止超時，強制終止。[/bold yellow]"
                )
                self.server_process.kill()
        else:
            self.dashboard.add_log("主應用程式未在運行。")
