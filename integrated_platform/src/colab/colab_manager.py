import time
from pathlib import Path
from IPython.display import display, HTML
from google.colab import output
from ..log_manager import LogManager
from ..ui.display_manager import DisplayManager

class ColabManager:
    """
    管理 Colab 環境中的所有操作。
    """
    def __init__(self, log_db_path: Path):
        self.log_manager = LogManager(log_db_path)
        self.display_manager = DisplayManager(self.log_manager)

    def start(self):
        """
        啟動 Colab 管理器。
        """
        self.display_manager.start()
        self.log_manager.log("INFO", "Colab 管理器已啟動。")

    def stop(self):
        """
        停止 Colab 管理器。
        """
        self.display_manager.stop()
        self.log_manager.log("INFO", "Colab 管理器已停止。")

    def create_public_portal(self, retries=3, delay=5):
        """
        嘗試建立一個 Colab 的公開服務入口，並提供重試機制。

        Args:
            retries (int): 嘗試次數。
            delay (int): 每次重試之間的延遲秒數。
        """
        for attempt in range(retries):
            try:
                output.serve_kernel_port_as_window(8000, path="/")
                self.log_manager.log("SUCCESS", "服務入口已建立。")
                display(HTML('<a href="/" target="_blank">點此開啟應用程式</a>'))
                return
            except Exception as e:
                self.log_manager.log("WARNING", f"建立服務入口失敗 (嘗試 {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(delay)
        self.log_manager.log("CRITICAL", "所有建立公開服務入口的嘗試均失敗。")

    def run_shell_command(self, command: str):
        """
        執行一個 shell 命令並記錄其輸出。

        Args:
            command (str): 要執行的命令。
        """
        import subprocess
        self.log_manager.log("INFO", f"正在執行命令: {command}")
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
        )
        for line in iter(process.stdout.readline, ""):
            self.log_manager.log("INFO", line.strip())
        process.stdout.close()
        return_code = process.wait()
        if return_code:
            self.log_manager.log("ERROR", f"命令 '{command}' 以返回碼 {return_code} 結束。")
        else:
            self.log_manager.log("INFO", f"命令 '{command}' 已成功執行。")
