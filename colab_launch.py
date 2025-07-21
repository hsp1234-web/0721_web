# colab_launch.py (簡化版 v3.0)
# 職責：專注於應用程式生命週期管理，不再負責環境設定。

import os
import sys
import subprocess
import time
import datetime
import traceback
from pathlib import Path
from zoneinfo import ZoneInfo

# --- 預處理：導入 TOML 解析庫 ---
IN_COLAB = "google.colab" in sys.modules
if IN_COLAB:
    from google.colab import output
else:
    class MockOutput:
        def serve_kernel_port_as_window(self, port, anchor_text):
            print("--- 非 Colab 環境 ---")
            print(f"伺服器應在 http://127.0.0.1:{port} 啟動")
            print(f"錨點文字: {anchor_text}")
    output = MockOutput()

try:
    import tomllib
except ImportError:
    try:
        import tomli as tomllib
    except ImportError:
        print("[💥 ERROR] 缺少 TOML 解析庫。請將 'tomli' 添加到 pyproject.toml。")
        sys.exit(1)

# --- 日誌管理系統 (維持不變) ---
class Logger:
    def __init__(self):
        self.timezone = ZoneInfo("Asia/Taipei")
    def _get_timestamp(self) -> str:
        return f"[{datetime.datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S')} Asia/Taipei]"
    def info(self, message: str):
        print(f"{self._get_timestamp()} [ℹ️ INFO] {message}")
    def success(self, message: str):
        print(f"{self._get_timestamp()} [✅ SUCCESS] {message}")
    def error(self, message: str, exc_info: bool = False):
        print(f"{self._get_timestamp()} [💥 ERROR] {message}")
        if exc_info:
            print(f"\n--- 錯誤軌跡開始 ---\n{traceback.format_exc()}\n--- 錯誤軌跡結束 ---")

logger = Logger()

# --- 版本宣告機制 (維持不變) ---
def get_project_version(project_root: Path) -> str:
    pyproject_path = project_root / "pyproject.toml"
    if not pyproject_path.is_file():
        return "版本未知 (找不到 pyproject.toml)"
    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)
        version = data.get("tool", {}).get("poetry", {}).get("version", "版本未知 (TOML 結構錯誤)")
        return version
    except Exception as e:
        return f"版本未知 (讀取失敗: {e})"

# --- 指揮中心：主部署函式 (已簡化) ---
def main():
    """
    在一個已準備好的環境中，協調應用程式的啟動。
    """
    project_root = Path.cwd() # 因為已被 deploy.sh 切換，cwd() 就是專案根目錄
    try:
        # 1. 版本宣告
        version = get_project_version(project_root)
        logger.info(f"正在啟動 鳳凰轉錄儀 v{version}...")
        logger.info(f"執行環境已由 deploy.sh 準備就緒。")

        # 2. 在背景啟動伺服器
        logger.info("正在背景啟動 FastAPI 伺服器...")
        log_file = open("server.log", "w")
        # 注意：此處不再需要 poetry run，因為 deploy.sh 已設定好環境
        subprocess.Popen(
            ["poetry", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"],
            stdout=log_file,
            stderr=log_file
        )
        time.sleep(5)
        logger.success("伺服器啟動指令已發送，日誌將寫入 server.log。")

        # 3. 產生公開網址
        logger.info("正在產生公開存取網址...")
        if IN_COLAB:
            from google.colab import output
            output.serve_kernel_port_as_window(8000, anchor_text="點擊這裡，在新分頁中開啟您的應用程式")
        else:
            logger.info("非 Colab 環境，跳過產生公開網址。")
        logger.success("部署完成！")

    except Exception as e:
        logger.error(f"應用程式啟動過程中發生致命錯誤: {e}", exc_info=True)
        sys.exit(1)

# --- 程式進入點 ---
if __name__ == "__main__":
    main()
