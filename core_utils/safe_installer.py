# -*- coding: utf-8 -*-
"""
核心工具：安全安裝器 (Safe Installer)
"""
import logging
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from .resource_monitor import is_resource_sufficient, load_resource_settings

# --- 日誌設定 ---
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)

def setup_logger(app_name: str) -> logging.Logger:
    """為指定的 App 設定一個詳細的日誌記錄器。"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = LOGS_DIR / f"install_{app_name}_{timestamp}.log"

    logger = logging.getLogger(f"SafeInstaller_{app_name}")
    logger.setLevel(logging.DEBUG)

    # 避免重複加入 handler
    if logger.hasHandlers():
        logger.handlers.clear()

    # 檔案日誌
    fh = logging.FileHandler(log_filename, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    fh.setFormatter(formatter)
    logger.addHandler(fh)

    # 控制台日誌
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

def install_packages(app_name: str, requirements_path: str, python_executable: str):
    """
    安全地安裝指定 requirements.txt 中的所有套件。

    Args:
        app_name: 正在安裝的 App 名稱 (e.g., "quant")。
        requirements_path: requirements.txt 檔案的路徑。
        python_executable: 目標虛擬環境的 Python 解譯器路徑。
    """
    logger = setup_logger(app_name)
    logger.info(f"--- 開始為 App '{app_name}' 進行安全安裝 ---")

    # 1. 載入資源設定
    settings = load_resource_settings()
    logger.info(f"成功載入資源設定檔。記憶體閾值: {settings['resource_monitoring']['memory_usage_threshold_percent']}%, 磁碟閾值: {settings['resource_monitoring']['min_disk_space_mb']}MB。")

    # 2. 讀取 requirements 檔案
    if not Path(requirements_path).exists():
        logger.warning(f"找不到 requirements 檔案: {requirements_path}。跳過安裝。")
        logger.info(f"--- App '{app_name}' 安裝結束 (無檔案) ---")
        return

    with open(requirements_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    packages = []
    for line in lines:
        # 去除行內註解 (從 '#' 開始的部分)
        line_content = line.split('#')[0].strip()
        # 只有在處理後還有內容時才加入列表
        if line_content:
            packages.append(line_content)

    logger.info(f"從 {requirements_path} 發現 {len(packages)} 個套件需要安裝。")

    # 3. 逐一套件安裝
    for i, package in enumerate(packages):
        logger.info(f"--- [{i+1}/{len(packages)}] 準備安裝: {package} ---")

        # 3.1. 安裝前檢查資源
        sufficient, message = is_resource_sufficient(settings)
        logger.debug(f"資源檢查結果: {message}")

        if not sufficient:
            logger.error(f"資源不足！{message}")
            logger.error(f"因資源不足，安裝程序已在安裝 '{package}' 前中止。")
            raise SystemExit(f"安裝失敗：App '{app_name}' 資源不足。")

        logger.info(f"資源充足。開始安裝 '{package}'...")

        # 3.2. 執行安裝命令
        try:
            # 使用 uv 來進行快速安裝
            command = [
                "uv", "pip", "install",
                "--python", python_executable,
                package
            ]

            start_time = time.monotonic()
            # 使用 subprocess.run 來執行命令並捕獲輸出
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                check=True,  # 如果返回非零結束代碼，則引發 CalledProcessError
                encoding='utf-8'
            )
            end_time = time.monotonic()
            duration = end_time - start_time

            logger.debug(f"'{package}' 安裝命令輸出:\n{result.stdout}")
            logger.info(f"✅ 套件 '{package}' 安裝成功，耗時: {duration:.2f} 秒。")

        except subprocess.CalledProcessError as e:
            logger.error(f"安裝套件 '{package}' 時發生錯誤。返回碼: {e.returncode}")
            logger.error(f"錯誤訊息:\n{e.stderr}")
            raise SystemExit(f"安裝失敗：App '{app_name}' 安裝套件 '{package}' 時出錯。")
        except Exception as e:
            logger.error(f"安裝套件 '{package}' 時發生未知錯誤: {e}")
            raise SystemExit(f"安裝失敗：App '{app_name}' 發生未知錯誤。")

    logger.info(f"--- App '{app_name}' 所有套件均已成功安裝 ---")


if __name__ == "__main__":
    # 這個區塊允許我們獨立測試安裝腳本
    # 使用方法: python -m core_utils.safe_installer <app_name> <req_path> <python_exec>
    if len(sys.argv) != 4:
        print("使用方法: python -m core_utils.safe_installer <app_name> <requirements_path> <python_executable>")
        sys.exit(1)

    # 在執行此腳本前，請確保已安裝 psutil 和 pyyaml
    # pip install psutil pyyaml

    app_name_arg = sys.argv[1]
    req_path_arg = sys.argv[2]
    python_exec_arg = sys.argv[3]

    install_packages(app_name_arg, req_path_arg, python_exec_arg)
