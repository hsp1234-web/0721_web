# colab_launch.py (生產級版本 v2.1)

import os
import sys
import subprocess
import time
import datetime
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

# --- 預處理：處理 Colab 環境的特殊性 ---
try:
    from google.colab import output
    IN_COLAB = True
except ImportError:
    IN_COLAB = False
    class MockOutput:
        def serve_kernel_port_as_window(self, port, anchor_text):
            print("--- 非 Colab 環境 ---")
            print(f"伺服器應在 http://127.0.0.1:{port} 啟動")
            print(f"錨點文字: {anchor_text}")
    output = MockOutput()

# --- Logger 類別定義 ---
class Logger:
    def __init__(self):
        self.timezone = ZoneInfo("Asia/Taipei")

    def _get_timestamp(self) -> str:
        timestamp = datetime.datetime.now(self.timezone).strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp} Asia/Taipei]"

    def info(self, message: str):
        print(f"{self._get_timestamp()} [ℹ️ INFO] {message}")

    def success(self, message: str):
        print(f"{self._get_timestamp()} [✅ SUCCESS] {message}")

    def error(self, message: str, exc_info: bool = False):
        print(f"{self._get_timestamp()} [💥 ERROR] {message}")
        if exc_info:
            detailed_traceback = traceback.format_exc()
            print(f"\n--- 錯誤軌跡開始 ---\n{detailed_traceback}\n--- 錯誤軌跡結束 ---")

logger = Logger()

# --- TOML 解析 ---
try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        logger.error("缺少 TOML 解析庫。請執行 'pip install tomli'")
        sys.exit(1)

def get_project_version(project_root: Path) -> str:
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        return "版本未知 (找不到 pyproject.toml)"

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    version = data.get("tool", {}).get("poetry", {}).get("version", "版本未知")
    return version

# --- 工具箱：經過加固的指令執行器 ---

def run_command(command: list, description: str, working_dir: Path):
    logger.info(f"正在執行: {description}...")
    try:
        result = subprocess.run(
            command,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            cwd=working_dir
        )
        logger.success(f"{description}... 完成。")
    except subprocess.CalledProcessError as e:
        logger.error(f"在執行 '{description}' 時發生致命錯誤:", exc_info=True)
        raise

# --- 指揮中心：主部署函式 ---

def main():
    project_root = None
    try:
        project_root = Path(__file__).parent.resolve()
        version = get_project_version(project_root)
        logger.info(f"正在啟動 鳳凰轉錄儀 v{version}...")
        logger.info(f"自動偵測到專案根目錄: {project_root}")

        if IN_COLAB:
            os.environ['PATH'] = f"/root/.local/bin:{os.environ['PATH']}"
            run_command(
                ["pip", "install", "poetry"],
                description="安裝 Poetry",
                working_dir=project_root
            )

        run_command(
            ["poetry", "install", "--no-root"],
            description="安裝專案依賴",
            working_dir=project_root
        )

        logger.info("正在背景啟動 FastAPI 伺服器...")
        log_file = open("server.log", "w")
        subprocess.Popen(
            ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
            cwd=project_root,
            stdout=log_file,
            stderr=log_file
        )
        time.sleep(5)
        logger.success("伺服器啟動指令已發送，日誌將寫入 server.log。")

        logger.info("正在產生公開存取網址...")
        output.serve_kernel_port_as_window(8000, anchor_text="點擊這裡，在新分頁中開啟您的應用程式")
        logger.success("部署完成！")

    except Exception as e:
        logger.error(f"部署過程中發生未預期的錯誤: {e}", exc_info=True)
        if project_root:
            logger.error(f"請檢查位於 '{project_root}' 的 pyproject.toml 設定。")
        sys.exit(1)

# --- 程式進入點 ---
if __name__ == "__main__":
    main()
