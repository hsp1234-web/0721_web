# -*- coding: utf-8 -*-
import asyncio
import subprocess
import sys
import sqlite3
from pathlib import Path
import os
import time
import json
from datetime import datetime
import shlex
import threading
import argparse

# --- 依賴預檢和自動安裝 ---
try:
    import pytz
    import psutil
    from IPython.display import display, clear_output
    import nest_asyncio
except ImportError:
    print("偵測到缺少核心依賴，正在自動安裝 (pytz, psutil, ipython, nest_asyncio)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pytz", "psutil", "ipython", "nest_asyncio"], check=True)
        print("依賴安裝成功。")
        import pytz
        import psutil
        from IPython.display import display, clear_output
        import nest_asyncio
    except Exception as e:
        print(f"自動安裝依賴失敗: {e}")
        print("請手動執行 'pip install pytz psutil ipython nest_asyncio' 後再試一次。")
        sys.exit(1)

from core_utils.commander_console import CommanderConsole
from core_utils.resource_monitor import is_resource_sufficient, load_resource_settings
from core_utils.report_generator import ReportGenerator

# --- 全域設定 ---
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
DB_FILE = LOGS_DIR / "logs.sqlite"
TAIWAN_TZ = pytz.timezone('Asia/Taipei')
APPS_DIR = Path("apps")

# 全域控制台物件
console = CommanderConsole()

def setup_database():
    """初始化 SQLite 資料庫和日誌表"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS phoenix_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            cpu_usage REAL,
            ram_usage REAL
        )
        """)
        conn.commit()

def log_event(level, message, cpu=None, ram=None):
    """將事件記錄到 TUI 和 SQLite 資料庫"""
    if not cpu: cpu = console.cpu_usage
    if not ram: ram = console.ram_usage

    console.add_log(f"[{level}] {message}")

    timestamp = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO phoenix_logs (timestamp, level, message, cpu_usage, ram_usage) VALUES (?, ?, ?, ?, ?)",
            (timestamp, level, message, cpu, ram)
        )
        conn.commit()

async def run_command_async_and_log(command: str, cwd: Path):
    """異步執行命令並將其輸出即時記錄到日誌中"""
    log_event("CMD", f"Executing: {command}")
    process = await asyncio.create_subprocess_shell(
        command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd
    )

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        decoded_line = line.decode('utf-8', errors='replace').strip()
        if decoded_line:
            log_event("SHELL", decoded_line)

    return_code = await process.wait()
    if return_code != 0:
        log_event("ERROR", f"Command failed with exit code {return_code}: {command}")
        raise RuntimeError(f"Command failed: {command}")

async def safe_install_packages(app_name: str, requirements_path: Path, python_executable: str):
    """安全地逐一安裝套件，並將日誌整合到主 TUI"""
    if not requirements_path.exists():
        log_event("WARN", f"找不到 {requirements_path}，跳過安裝。")
        return

    with open(requirements_path, "r") as f:
        packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    log_event("BATTLE", f"開始為 {app_name} 安裝 {len(packages)} 個依賴。")

    settings = load_resource_settings()
    for i, package in enumerate(packages):
        console.update_status_tag(f"[{app_name}] 安裝依賴: {i+1}/{len(packages)}")
        log_event("PROGRESS", f"正在安裝 {i+1}/{len(packages)}: {package}")

        sufficient, message = is_resource_sufficient(settings)
        if not sufficient:
            log_event("ERROR", f"資源不足，中止安裝: {message}")
            raise RuntimeError(f"Resource insufficient for {app_name}: {message}")

        try:
            command = f"uv pip install --python {shlex.quote(python_executable)} {package}"
            await run_command_async_and_log(command, APPS_DIR.parent)
        except Exception as e:
            log_event("ERROR", f"安裝套件 '{package}' 失敗: {e}")
            raise

# --- 核心啟動邏輯 ---
async def manage_app_lifecycle(app_name, port, app_status):
    """完整的應用生命週期管理：安裝、啟動"""
    app_status[app_name] = "pending"
    venv_path = APPS_DIR / app_name / ".venv"
    python_executable = str(venv_path / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'))

    try:
        # --- 1. 環境準備 ---
        app_status[app_name] = "installing"
        console.update_status_tag(f"[{app_name}] 準備虛擬環境")
        if not venv_path.exists():
            await run_command_async_and_log(f"uv venv {shlex.quote(str(venv_path))}", APPS_DIR.parent)

        # --- 2. 安裝依賴 ---
        req_file = APPS_DIR / app_name / "requirements.txt"
        await safe_install_packages(app_name, req_file, python_executable)

        # 安裝大型依賴 (如果存在)
        large_req_file = APPS_DIR / app_name / "requirements.large.txt"
        if large_req_file.exists():
            await safe_install_packages(f"{app_name}-large", large_req_file, python_executable)

        log_event("SUCCESS", f"[{app_name}] 所有依賴已成功安裝。")

        # --- 3. 啟動服務 ---
        app_status[app_name] = "starting"
        console.update_status_tag(f"[{app_name}] 啟動服務中...")
        env = os.environ.copy()
        env["PORT"] = str(port)

        log_file = LOGS_DIR / f"{app_name}_service.log"
        main_script_path = APPS_DIR / app_name / "main.py"
        with open(log_file, "w") as f:
            subprocess.Popen(
                [python_executable, str(main_script_path)],
                env=env,
                stdout=f, stderr=subprocess.STDOUT
            )

        await asyncio.sleep(10) # 給予服務啟動時間
        app_status[app_name] = "running"
        log_event("SUCCESS", f"[{app_name}] 服務已在背景啟動 (日誌: {log_file})")

    except Exception as e:
        app_status[app_name] = "failed"
        log_event("CRITICAL", f"管理應用 '{app_name}' 時發生嚴重錯誤: {e}")
        raise

def load_config():
    """載入設定檔"""
    config_path = Path("config.json")
    if not config_path.exists():
        # 如果設定檔不存在，回傳一個合理的預設值
        return {
            "FAST_TEST_MODE": True,
            "TIMEZONE": "Asia/Taipei"
        }
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

async def main_logic(config: dict):
    """核心的循序啟動邏輯"""
    is_full_mode = not config.get("FAST_TEST_MODE", True)

    if is_full_mode:
        log_event("BATTLE", "鳳凰之心 v18.0 [完整模式] 啟動序列開始。")
    else:
        log_event("BATTLE", "鳳凰之心 v18.0 [快速測試模式] 啟動序列開始。")

    log_event("INFO", "系統環境預檢完成。")

    if not is_full_mode:
        log_event("INFO", "[快速測試模式] 跳過所有 App 的安裝與啟動。")
        await asyncio.sleep(5) # 模擬一些工作負載
        log_event("SUCCESS", "快速測試流程驗證成功。")
        console.update_status_tag("[快速測試通過]")
        return

    apps_status = { "quant": "pending", "transcriber": "pending" }
    app_configs = [
        {"name": "quant", "port": 8001},
        {"name": "transcriber", "port": 8002}
    ]

    # 循序執行以避免資源競爭
    for config in app_configs:
        await manage_app_lifecycle(config['name'], config['port'], apps_status)

    if all(status == "running" for status in apps_status.values()):
        log_event("SUCCESS", "所有核心服務已成功啟動。")
        console.update_status_tag("[服務運行中]")
    else:
        log_event("ERROR", "部分服務啟動失敗，請檢查日誌。")
        console.update_status_tag("[啟動失敗]")

# --- 主程序 ---
def performance_logger_thread():
    """一個獨立的執行緒，專門用來將效能數據寫入資料庫"""
    while not console._stop_event.is_set():
        timestamp = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO phoenix_logs (timestamp, level, message, cpu_usage, ram_usage) VALUES (?, ?, ?, ?, ?)",
                (timestamp, "PERF", "performance_snapshot", console.cpu_usage, console.ram_usage)
            )
            conn.commit()
        time.sleep(1) # 每秒記錄一次

async def main():
    """包含 TUI 和休眠邏輯的主異步函數"""
    if DB_FILE.exists():
        os.remove(DB_FILE)
    setup_database()

    config = load_config()
    console.start()

    # 啟動專門的效能日誌記錄執行緒
    perf_thread = threading.Thread(target=performance_logger_thread, daemon=True)
    perf_thread.start()

    try:
        await main_logic(config)
        log_event("INFO", "任務流程執行完畢，系統進入待命狀態。")
        # 在完整模式下才長時間休眠
        if not config.get("FAST_TEST_MODE", True):
            await asyncio.sleep(3600)
    except Exception as e:
        log_event("CRITICAL", f"主程序發生未預期錯誤: {e}")
    finally:
        console.stop("程序結束。")
        # 確保效能日誌執行緒也已停止
        perf_thread.join(timeout=1.5)

        # --- 報告生成 ---
        log_event("INFO", "開始生成最終報告...")
        try:
            config_path = Path("config.json")
            if config_path.exists():
                generator = ReportGenerator(db_path=DB_FILE, config_path=config_path)
                generator.generate_all_reports()
                log_event("SUCCESS", "所有報告已成功生成。")
            else:
                log_event("WARN", "找不到設定檔 (config.json)，無法生成報告。")
        except Exception as e:
            log_event("CRITICAL", f"生成報告時發生嚴重錯誤: {e}")

if __name__ == "__main__":

    try:
        # 確保 uv 已安裝
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("錯誤: 核心工具 'uv' 未安裝。請先執行 'pip install uv'。")
        sys.exit(1)

    if 'IPython' in sys.modules:
        nest_asyncio.apply()

    try:
        asyncio.run(main(args))
    except KeyboardInterrupt:
        pass
