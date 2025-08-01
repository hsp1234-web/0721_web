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
import signal
import shutil

# --- 依賴預檢和自動安裝 ---
try:
    import pytz
    import nest_asyncio
    from aiohttp import web
except ImportError:
    print("偵測到缺少核心依賴，正在自動安裝 (pytz, nest_asyncio, aiohttp)...")
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", "pytz", "nest_asyncio", "aiohttp"], check=True)
        print("依賴安裝成功。")
        import pytz
        import nest_asyncio
        from aiohttp import web
    except Exception as e:
        print(f"自動安裝依賴失敗: {e}")
        print("請手動執行 'pip install pytz nest_asyncio aiohttp' 後再試一次。")
        sys.exit(1)

# 解決腳本移動到 scripts/ 後的路徑問題
sys.path.insert(0, str(Path(__file__).parent.parent))

from core_utils.commander_console import CommanderConsole
from core_utils.resource_monitor import is_resource_sufficient, load_resource_settings

# --- 全域設定 ---
LOGS_DIR = Path("logs")
LOGS_DIR.mkdir(exist_ok=True)
DB_FILE = None # 將由命令列參數提供
TAIWAN_TZ = pytz.timezone('Asia/Taipei')
APPS_DIR = Path("apps")

# 全域控制台物件
console = CommanderConsole()

# 全域關閉事件
shutdown_event = asyncio.Event()

def setup_database():
    """初始化 SQLite 資料庫，建立前端所需的所有表。"""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        # 確保從乾淨的狀態開始
        cursor.execute("DROP TABLE IF EXISTS phoenix_logs")
        cursor.execute("DROP TABLE IF EXISTS status_table")
        cursor.execute("""
        CREATE TABLE phoenix_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            cpu_usage REAL,
            ram_usage REAL
        )""")
        cursor.execute("""
        CREATE TABLE status_table (
            id INTEGER PRIMARY KEY,
            current_stage TEXT,
            apps_status TEXT,
            action_url TEXT,
            cpu_usage REAL,
            ram_usage REAL
        )""")
        # 插入唯一的狀態行
        cursor.execute("INSERT OR IGNORE INTO status_table (id) VALUES (1)")
        conn.commit()

def update_status(stage=None, apps_status=None, url=None, cpu=None, ram=None):
    """安全地更新 status_table 中的狀態。"""
    if not DB_FILE:
        return
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            if stage is not None:
                cursor.execute("UPDATE status_table SET current_stage = ? WHERE id = 1", (stage,))
            if apps_status is not None:
                cursor.execute("UPDATE status_table SET apps_status = ? WHERE id = 1", (json.dumps(apps_status),))
            if url is not None:
                cursor.execute("UPDATE status_table SET action_url = ? WHERE id = 1", (url,))
            if cpu is not None:
                cursor.execute("UPDATE status_table SET cpu_usage = ? WHERE id = 1", (cpu,))
            if ram is not None:
                cursor.execute("UPDATE status_table SET ram_usage = ? WHERE id = 1", (ram,))
            conn.commit()
    except Exception as e:
        # 在啟動初期，TUI 可能還不存在，所以用 print
        print(f"Error updating status db: {e}")


def log_event(level, message, cpu=None, ram=None):
    """將事件記錄到 TUI 和 SQLite 資料庫"""
    if not cpu:
        cpu = console.cpu_usage
    if not ram:
        ram = console.ram_usage

    console.add_log(f"[{level}] {message}")

    if not DB_FILE:
        return
    timestamp = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO phoenix_logs (timestamp, level, message, cpu_usage, ram_usage) VALUES (?, ?, ?, ?, ?)",
                (timestamp, level, message, cpu, ram)
            )
            conn.commit()
    except Exception as e:
        print(f"Error logging to db: {e}")

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

    with open(requirements_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    packages = []
    for line in lines:
        # 去除行內註解 (從 '#' 開始的部分)
        line_content = line.split('#')[0].strip()
        # 只有在處理後還有內容時才加入列表
        if line_content:
            packages.append(line_content)

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
    update_status(apps_status=app_status)
    venv_path = APPS_DIR / app_name / ".venv"
    # 將 python_executable 的路徑解析為絕對路徑。
    # 這樣可以避免在 subprocess.Popen 中因 cwd (目前工作目錄) 的改變而導致的路徑找不到問題。
    python_executable = str(venv_path.resolve() / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python'))

    try:
        # --- 1. 環境準備 ---
        app_status[app_name] = "installing"
        update_status(stage=f"[{app_name}] 準備環境", apps_status=app_status)
        console.update_status_tag(f"[{app_name}] 準備虛擬環境")
        if not venv_path.exists():
            # 使用 venv_path 的絕對路徑來建立 venv
            await run_command_async_and_log(f"uv venv {shlex.quote(str(venv_path.resolve()))}", APPS_DIR.parent)

        # --- 2. 安裝依賴 ---
        update_status(stage=f"[{app_name}] 安裝依賴")
        req_file = APPS_DIR / app_name / "requirements.txt"
        await safe_install_packages(app_name, req_file, python_executable)

        # 安裝大型依賴 (如果存在)
        large_req_file = APPS_DIR / app_name / "requirements.large.txt"
        if large_req_file.exists():
            await safe_install_packages(f"{app_name}-large", large_req_file, python_executable)

        log_event("SUCCESS", f"[{app_name}] 所有依賴已成功安裝。")

        # --- 3. 啟動服務 ---
        app_status[app_name] = "starting"
        update_status(stage=f"[{app_name}] 啟動服務", apps_status=app_status)
        console.update_status_tag(f"[{app_name}] 啟動服務中...")
        env = os.environ.copy()
        env["PORT"] = str(port)

        log_file = LOGS_DIR / f"{app_name}_service.log"
        # 從 app/{app_name}/main.py 找到 FastAPI app instance, 預設為 "app"
        # Gunicorn 指令: python -m gunicorn main:app --workers 2 --worker-class uvicorn.workers.UvicornWorker --bind 0.0.0.0:PORT
        # 改為使用 `python -m gunicorn`，這種方式更可靠，可以避免因環境問題導致找不到 gunicorn 執行檔的問題。
        gunicorn_command = [
            python_executable, # 使用虛擬環境的 python
            "-m", "gunicorn",
            "main:app",  # 指向 main.py 中的 app = FastAPI()
            "--workers", "2",  # 啟動 2 個工人進程，可以根據需要調整
            "--worker-class", "uvicorn.workers.UvicornWorker",  # 使用 uvicorn 作為工人
            "--bind", f"0.0.0.0:{port}",  # 綁定端口
            "--log-level", "info", # 設置日誌級別
            "--access-logfile", "-", # 將訪問日誌輸出到 stdout
            "--error-logfile", "-", # 將錯誤日誌輸出到 stdout
        ]
        log_event("INFO", f"使用 Gunicorn 啟動服務: {' '.join(gunicorn_command)}")

        with open(log_file, "w") as f:
            subprocess.Popen(
                gunicorn_command,
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                cwd=APPS_DIR / app_name, # 將工作目錄切換到 app 目錄下
            )

        await asyncio.sleep(10) # 給予服務啟動時間
        app_status[app_name] = "running"
        update_status(apps_status=app_status)
        log_event("SUCCESS", f"[{app_name}] 服務已在背景啟動 (日誌: {log_file})")

    except Exception as e:
        app_status[app_name] = "failed"
        update_status(apps_status=app_status)
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
    """核心的兩階段、非同步啟動邏輯"""
    is_full_mode = not config.get("FAST_TEST_MODE", True)

    # 定義所有應用，將主儀表板放在第一位
    app_configs = [
        {"name": "main_dashboard", "port": 8000},
        {"name": "quant", "port": 8001},
        {"name": "transcriber", "port": 8002}
    ]
    apps_status = {app["name"]: "pending" for app in app_configs}

    if is_full_mode:
        log_event("BATTLE", "鳳凰之心 v19.0 [完整模式] 啟動序列開始。")
        update_status(stage="系統啟動中 [完整模式]", apps_status=apps_status)
    else:
        log_event("BATTLE", "鳳凰之心 v19.0 [快速測試模式] 啟動序列開始。")
        update_status(stage="系統啟動中 [快速模式]", apps_status=apps_status)

    log_event("INFO", "系統環境預檢完成。")

    if not is_full_mode:
        log_event("INFO", "[快速測試模式] 跳過所有 App 的安裝與啟動。")
        update_status(stage="快速測試模式")
        await asyncio.sleep(5)
        log_event("SUCCESS", "快速測試流程驗證成功。")
        console.update_status_tag("[快速測試通過]")
        update_status(stage="快速測試通過")
        return

    # --- 兩階段啟動 ---

    # 階段一: 優先啟動主儀表板
    update_status(stage="階段一：啟動主儀表板")
    dashboard_config = app_configs[0]
    try:
        await manage_app_lifecycle(dashboard_config['name'], dashboard_config['port'], apps_status)
        log_event("SUCCESS", f"主儀表板 ({dashboard_config['name']}) 已成功啟動。")
        update_status(stage="主儀表板運行中，準備啟動背景服務")

    except Exception as e:
        log_event("CRITICAL", f"主儀表板 ({dashboard_config['name']}) 啟動失敗: {e}，中止所有操作。")
        console.update_status_tag("[主儀表板啟動失敗]")
        update_status(stage="主儀表板啟動失敗")
        return # 主儀表板失敗，後續流程無法進行

    # 階段二: 在背景並行啟動其他服務
    update_status(stage="階段二：並行啟動背景服務")
    background_apps = app_configs[1:]
    background_tasks = []
    for app_config in background_apps:
        task = asyncio.create_task(
            manage_app_lifecycle(app_config['name'], app_config['port'], apps_status)
        )
        background_tasks.append(task)

    # 等待所有背景任務完成
    if background_tasks:
        await asyncio.gather(*background_tasks)

    # 檢查最終狀態
    final_statuses = {name: status for name, status in apps_status.items() if name != dashboard_config['name']}
    if all(status == "running" for status in final_statuses.values()):
        log_event("SUCCESS", "所有核心服務已成功啟動。")
        console.update_status_tag("[所有服務運行中]")
        update_status(stage="所有服務運行中")
    else:
        log_event("WARN", "部分背景服務啟動失敗，請檢查日誌。")
        console.update_status_tag("[部分服務失敗]")
        update_status(stage="部分服務失敗")

    # 進入待命狀態，等待關閉事件
    log_event("INFO", "任務流程執行完畢，系統進入待命狀態。等待關閉指令...")
    try:
        await shutdown_event.wait()
        log_event("INFO", "關閉事件已觸發，結束待命狀態。")
    except asyncio.CancelledError:
        log_event("INFO", "系統待命狀態被外部信號中斷。")

# --- 主程序 ---
def performance_logger_thread():
    """一個獨立的執行緒，專門用來將效能數據寫入資料庫"""
    # 這裡我們不傳入 settings，而是在執行緒內部讀取一次性的設定
    config = load_config()
    refresh_interval = config.get("PERFORMANCE_MONITOR_RATE_SECONDS", 1.0)

    while not console._stop_event.is_set():
        # 更新 status_table
        update_status(cpu=console.cpu_usage, ram=console.ram_usage)

        # 也將其記錄到日誌表
        timestamp = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        try:
            with sqlite3.connect(DB_FILE) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO phoenix_logs (timestamp, level, message, cpu_usage, ram_usage) VALUES (?, ?, ?, ?, ?)",
                    (timestamp, "PERF", "performance_snapshot", console.cpu_usage, console.ram_usage)
                )
                conn.commit()
        except Exception as e:
            print(f"Error in perf logger: {e}")

        time.sleep(refresh_interval)

# --- API 伺服器邏輯 ---
async def get_status_api(request):
    """API 端點，用於獲取當前的完整狀態"""
    try:
        with sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 獲取主狀態
            cursor.execute("SELECT * FROM status_table WHERE id = 1")
            status_data = cursor.fetchone()

            # 獲取日誌等級設定
            config = load_config()
            levels_to_show = config.get("LOG_LEVELS_TO_SHOW", {})

            # 預設顯示所有等級，除非設定明確為 False
            if not levels_to_show:
                 # 如果 LOG_LEVELS_TO_SHOW 是空的或不存在，則顯示所有等級
                 allowed_levels_clause = ""
            else:
                allowed_levels = [level for level, show in levels_to_show.items() if show]
                if not allowed_levels:
                    # 如果所有等級都被設置為 False，則不顯示任何日誌
                    logs_data = []
                    allowed_levels_clause = "WHERE 1=0" # A trick to get no results
                else:
                    placeholders = ','.join('?' for _ in allowed_levels)
                    allowed_levels_clause = f"WHERE level IN ({placeholders})"

            if 'logs_data' not in locals():
                log_display_lines = config.get("LOG_DISPLAY_LINES", 20)
                query = f"SELECT timestamp, level, message FROM phoenix_logs {allowed_levels_clause} ORDER BY id DESC LIMIT ?"

                params = []
                if allowed_levels_clause and "WHERE 1=0" not in allowed_levels_clause:
                    params.extend(allowed_levels)
                params.append(log_display_lines)

                cursor.execute(query, tuple(params))
                logs_data = cursor.fetchall()

        if not status_data:
            return web.json_response({"error": "Status not found"}, status=404)

        # 查詢最近 20 筆效能數據
        cursor.execute("SELECT cpu_usage, ram_usage FROM phoenix_logs WHERE level = 'PERF' ORDER BY id DESC LIMIT 20")
        perf_history_data = cursor.fetchall()
        # 將其反轉，以便從舊到新排序，適合趨勢圖
        perf_history_data.reverse()

        response_data = {
            "status": dict(status_data),
            "logs": [dict(log) for log in logs_data],
            "performance_history": [dict(row) for row in perf_history_data]
        }
        return web.json_response(response_data)

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)

async def shutdown_api(request):
    """API 端點，用於觸發優雅關閉。"""
    log_event("BATTLE", "接收到 API 關閉指令，準備關閉服務...")
    shutdown_event.set()
    return web.json_response({"status": "shutdown_initiated"}, status=200)

async def run_api_server():
    """運行 aiohttp API 伺服器"""
    app = web.Application()
    app.router.add_get("/api/v1/status", get_status_api)
    app.router.add_post("/api/v1/shutdown", shutdown_api)
    runner = web.AppRunner(app)
    await runner.setup()
    # 使用一個前端不太可能衝突的埠
    site = web.TCPSite(runner, 'localhost', 8088)
    try:
        await site.start()
        log_event("INFO", "狀態 API 伺服器已在 http://localhost:8088 啟動")
        # 保持伺服器運行
        while True:
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        log_event("INFO", "狀態 API 伺服器正在關閉...")
    finally:
        await runner.cleanup()


async def main(db_path: Path):
    """包含 TUI、API 和休眠邏輯的主異步函數"""
    global DB_FILE
    DB_FILE = db_path

    if DB_FILE.exists():
        os.remove(DB_FILE)
    setup_database()

    config = load_config()
    console.start()

    # 啟動專門的效能日誌記錄執行緒
    perf_thread = threading.Thread(target=performance_logger_thread, daemon=True)
    perf_thread.start()

    # 建立 API 伺服器任務
    api_task = asyncio.create_task(run_api_server())

    # 將主邏輯包裝成一個任務，以便可以取消它
    main_logic_task = asyncio.create_task(main_logic(config))

    # --- 優雅關閉處理 ---
    loop = asyncio.get_running_loop()
    def shutdown_handler(sig):
        log_event("INFO", f"接收到關閉信號 {sig.name}。正在取消主任務...")
        if not main_logic_task.done():
            main_logic_task.cancel()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, shutdown_handler, sig)
    # --- 優雅關閉處理結束 ---

    try:
        await main_logic_task
    except asyncio.CancelledError:
        log_event("INFO", "主任務已被取消。")
    except Exception as e:
        log_event("CRITICAL", f"主程序發生未預期錯誤: {e}")
    finally:
        console.stop("程序結束。")
        # 確保效能日誌執行緒也已停止
        perf_thread.join(timeout=1.5)

        # 停止 API 伺服器
        if not api_task.done():
            api_task.cancel()
        await asyncio.sleep(0.1) # 給予取消操作一點時間

        # --- 報告生成、中文化與歸檔 ---
        log_event("INFO", "===== 開始生成並處理最終報告 =====")
        try:
            # 步驟 1: 生成原始報告 (generate_report.py)
            # (此處恢復被意外刪除的報告生成邏輯)
            report_deps = ["pandas", "pytz", "sparklines", "tabulate"]
            log_event("INFO", f"正在為報告生成器安裝依賴: {', '.join(report_deps)}")
            install_cmd = [sys.executable, "-m", "pip", "install", "-q", *report_deps]
            dep_result = subprocess.run(install_cmd, capture_output=True, text=True, encoding='utf-8')
            if dep_result.returncode == 0:
                log_event("SUCCESS", "報告生成器依賴已就緒。")
            else:
                log_event("ERROR", "報告生成器依賴安裝失敗。")
                # 記錄錯誤但不在此處退出，嘗試繼續執行
                if dep_result.stderr:
                    for line in dep_result.stderr.strip().split('\n'):
                        if line: log_event("ERROR", f"[PipInstaller] {line}")

            config_path = Path("config.json")
            if config_path.exists() and DB_FILE.exists():
                report_cmd = [
                    sys.executable, "scripts/generate_report.py",
                    "--db-file", str(DB_FILE),
                    "--config-file", str(config_path)
                ]
                log_event("CMD", f"Executing: {' '.join(report_cmd)}")
                result = subprocess.run(report_cmd, capture_output=True, text=True, encoding='utf-8')
                log_event("INFO", f"報告生成腳本執行完畢，返回碼: {result.returncode}")
                if result.stdout:
                    for line in result.stdout.strip().split('\n'):
                        if line: log_event("INFO", f"[ReportGenerator-STDOUT] {line}")
                if result.stderr:
                    for line in result.stderr.strip().split('\n'):
                        if line: log_event("ERROR", f"[ReportGenerator-STDERR] {line}")
                if result.returncode == 0:
                    log_event("SUCCESS", "所有原始報告已成功生成。")
                else:
                    log_event("ERROR", "報告生成腳本執行失敗。")
            else:
                log_event("ERROR", "找不到 config.json 或 state.db，無法生成報告。")


            # 步驟 2. 處理報告 (中文化、歸檔)
            config = load_config()
            project_path = Path.cwd() # launch.py 的工作目錄就是專案根目錄
            archive_folder_name = config.get("LOG_ARCHIVE_FOLDER_NAME")
            timezone_str = config.get("TIMEZONE", "Asia/Taipei")

            logs_dir = project_path / "logs"
            if not logs_dir.is_dir():
                log_event("ERROR", f"找不到日誌目錄 {logs_dir}，無法處理報告。")
                return

            # --- 整合報告 ---
            log_event("INFO", "合併報告分卷...")
            original_reports = ["summary_report.md", "performance_report.md", "detailed_log_report.md"]
            consolidated_content = f"# 鳳凰之心最終任務報告\n\n**報告產生時間:** {datetime.now(pytz.timezone(timezone_str)).isoformat()}\n\n---\n\n"
            final_report_path = project_path / "最終運行報告.md"

            for report_file in original_reports:
                report_path = logs_dir / report_file
                if report_path.exists():
                    consolidated_content += f"## 原始報告: {report_file}\n\n"
                    consolidated_content += report_path.read_text(encoding='utf-8')
                    consolidated_content += "\n\n---\n\n"

            if len(consolidated_content) > 200:
                final_report_path.write_text(consolidated_content, encoding='utf-8')
                log_event("SUCCESS", "整合報告已生成: 最終運行報告.md")

            # --- 重新命名 ---
            log_event("INFO", "將報告檔案重新命名為中文...")
            rename_map = {
                "summary_report.md": "任務總結報告.md",
                "performance_report.md": "效能分析報告.md",
                "detailed_log_report.md": "詳細日誌報告.md"
            }
            renamed_paths_for_archive = []
            for old_name, new_name in rename_map.items():
                old_path = logs_dir / old_name
                new_path = logs_dir / new_name
                if old_path.exists():
                    old_path.rename(new_path)
                    log_event("INFO", f"  - 已重新命名: {old_name} -> {new_name}")
                    renamed_paths_for_archive.append(new_path)

            # --- 步驟 3: 歸檔報告 ---
            log_event("INFO", "===== 開始歸檔最終報告 =====")
            log_event("CRITICAL", f"準備歸檔，讀取到的資料夾名稱為: '{archive_folder_name}'")
            if not archive_folder_name:
                log_event("CRITICAL", "歸檔資料夾名稱為空，因此跳過歸檔。")
            else:
                try:
                    # 在 launch.py 中，CWD 就是專案根目錄，即 project_path
                    archive_base_path = project_path / archive_folder_name
                    archive_base_path.mkdir(exist_ok=True)

                    tz = pytz.timezone(timezone_str)
                    timestamp_folder_name = datetime.now(tz).isoformat()
                    archive_target_path = archive_base_path / timestamp_folder_name
                    archive_target_path.mkdir()

                    files_to_archive_names = [
                        "任務總結報告.md",
                        "效能分析報告.md",
                        "詳細日誌報告.md",
                        "最終運行報告.md"
                    ]

                    for filename in files_to_archive_names:
                        # 檢查 logs 目錄和專案根目錄
                        source_path = logs_dir / filename
                        if not source_path.exists():
                            source_path = project_path / filename

                        if source_path.exists():
                            shutil.move(str(source_path), str(archive_target_path / filename))
                            log_event("INFO", f"  - 已歸檔: {filename}")
                        else:
                            log_event("WARN", f"  - 警告: 未找到報告檔案 {filename}，無法歸檔。")

                    log_event("SUCCESS", f"✅ 所有報告已歸檔至: {archive_target_path}")

                except Exception as e:
                    import traceback
                    log_event("CRITICAL", f"歸檔報告時發生嚴重錯誤: {e}\n{traceback.format_exc()}")

        except Exception as e:
            import traceback
            log_event("CRITICAL", f"報告處理過程中發生嚴重錯誤: {e}\n{traceback.format_exc()}")
            sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="鳳凰之心 v18.0 後端啟動器")
    parser.add_argument("--db-file", type=Path, required=True, help="SQLite 資料庫的絕對路徑")
    args = parser.parse_args()

    try:
        # 確保 uv 已安裝
        subprocess.run(["uv", "--version"], check=True, capture_output=True)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("錯誤: 核心工具 'uv' 未安裝。請先執行 'pip install uv'。")
        sys.exit(1)

    if 'IPython' in sys.modules:
        nest_asyncio.apply()

    try:
        asyncio.run(main(args.db_file))
    except KeyboardInterrupt:
        pass
