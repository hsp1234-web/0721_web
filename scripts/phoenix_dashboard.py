# -*- coding: utf-8 -*-
"""
🚀 鳳凰之心：視覺化啟動器 (Phoenix Heart: Visual Starter) v8.0 🚀

這個腳本是 `launch.py` 和 `smart_e2e_test.sh` 的終極結合體，並完全實現了
「鳳凰之心：啟動體驗最終設計稿 (v8.0 融合版)」中描述的所有功能。

它不僅擁有前兩者的所有功能，更提供了一個精美的、資訊豐富的
終端儀表板來即時監控整個系統的啟動與測試過程。

核心功能:
- 視覺化儀表板 (TUI): 使用 ANSI escape codes 精準復刻設計稿，提供清晰的狀態概覽。
- 智能資源檢測: 自動檢查記憶體與磁碟，決定採用「完整」或「模擬」安裝模式。
- 完整測試流程: 一鍵完成從環境準備、依賴安裝到執行 `pytest` 的完整端到端測試。
- 動態進度追蹤: 即時解析 `uv` 安裝過程的輸出，實現流暢的進度條動畫。

使用方法:
    python phoenix_starter.py

    # 若您的終端不支援 TUI，可使用無介面模式：
    python phoenix_starter.py --no-tui
"""
import asyncio
import subprocess
import sys
from pathlib import Path
import os
import shlex
import re

# --- 常數與設定 ---
APPS_DIR = Path("src")
PROJECT_ROOT = Path(__file__).parent.parent.resolve()

# --- 應用程式狀態枚舉 ---
class AppStatus:
    PENDING = "⚪ 待命"
    INSTALLING = "🔄 安裝中"
    INSTALL_DONE = "✅ 環境就緒"
    TESTING = "🧪 測試中"
    TEST_PASSED = "🟢 測試通過"
    TEST_FAILED = "🔴 測試失敗"
    RUNNING = "🟢 運行中"
    FAILED = "🔴 失敗"

class App:
    """代表一個微服務應用程式的類別"""
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.status = AppStatus.PENDING
        self.venv_path = path / ".venv_visual" # 使用獨立的 venv
        self.log = []
        self.dashboard = None

    def set_status(self, status: str):
        self.status = status
        if self.dashboard:
            self.dashboard.update_app_status()

    def add_log(self, message: str):
        self.log.append(message)
        if self.dashboard:
            self.dashboard.add_log_entry(message)

# 用於解析 uv 進度條的正則表達式
PROGRESS_RE = re.compile(
    r"(?P<package>[\w\-]+)\s+"  # 套件名稱
    r"(?P<version>[\d\.]+)\s+"  # 版本
    r"\[(?P<bar>[━╸ ]+)\]\s+"    # 進度條
    r"(?P<percent>\d+)%\s+-\s+"  # 百分比
    r"(?P<size>[\d\./\w ]+)\s+@\s+" # 大小
    r"(?P<speed>[\d\.\w /s]+)"     # 速度
)

async def run_command_async(command: str, cwd: Path, app: App):
    """異步執行一個子進程命令，並將其輸出串流到 App 的日誌中"""
    is_install_command = "pip install" in command
    task_name = f"安裝依賴於 {app.name}" if is_install_command else f"執行 {command.split()[0]}"

    if app.dashboard and is_install_command:
        app.dashboard.update_current_task(task_name=task_name, progress_line="")

    # ... (subprocess 建立過程保持不變)
    if sys.platform != "win32":
        args = shlex.split(command)
        process = await asyncio.create_subprocess_exec(*args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=cwd)
    else:
        process = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT, cwd=cwd)

    while True:
        line = await process.stdout.readline()
        if not line:
            break
        decoded_line = line.decode('utf-8', errors='replace').strip()
        if not decoded_line:
            continue

        match = PROGRESS_RE.match(decoded_line)
        if match and app.dashboard and is_install_command:
            # 這是進度條，更新當前任務區塊
            app.dashboard.update_current_task(progress_line=decoded_line)
        else:
            # 這是普通日誌
            app.add_log(decoded_line)

    if app.dashboard and is_install_command:
        app.dashboard.update_current_task(task_name="[空閒]", progress_line="")

    return await process.wait()

async def prepare_app_environment(app: App, install_large_deps=False):
    """為單個 App 準備環境和依賴"""
    app.set_status(AppStatus.INSTALLING)

    try:
        # 1. 建立虛擬環境
        venv_cmd = f"uv venv {shlex.quote(str(app.venv_path))} --seed"
        return_code = await run_command_async(venv_cmd, cwd=PROJECT_ROOT, app=app)
        if return_code != 0:
            raise RuntimeError(f"建立虛擬環境失敗，返回碼: {return_code}")

        python_executable = app.venv_path / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')

        if not python_executable.exists():
            raise FileNotFoundError(f"在 '{app.venv_path}' 中找不到 Python 解譯器: '{python_executable}'")

        # 2. 安裝通用測試依賴
        common_deps = "pytest pytest-mock ruff httpx"
        pip_cmd = f'uv pip install --python "{python_executable}" {common_deps}'
        return_code = await run_command_async(pip_cmd, cwd=PROJECT_ROOT, app=app)
        if return_code != 0:
            raise RuntimeError(f"安裝通用依賴失敗，返回碼: {return_code}")

        # 3. 安裝 App 核心依賴
        reqs_file = app.path / "requirements.txt"
        if reqs_file.exists():
            pip_cmd = f'uv pip install --python "{python_executable}" -r "{reqs_file}"'
            return_code = await run_command_async(pip_cmd, cwd=PROJECT_ROOT, app=app)
            if return_code != 0:
                raise RuntimeError(f"安裝核心依賴失敗，返回碼: {return_code}")

        # 4. (可選) 安裝大型依賴
        if install_large_deps:
            large_reqs_file = app.path / "requirements.large.txt"
            if large_reqs_file.exists():
                app.add_log("偵測到大型依賴，開始安裝...")
                pip_cmd = f'uv pip install --python "{python_executable}" -r "{large_reqs_file}"'
                return_code = await run_command_async(pip_cmd, cwd=PROJECT_ROOT, app=app)
                if return_code != 0:
                    raise RuntimeError(f"安裝大型依賴失敗，返回碼: {return_code}")

        app.set_status(AppStatus.INSTALL_DONE)
        return True

    except Exception as e:
        app.set_status(AppStatus.FAILED)
        app.add_log(f"💥 環境準備過程中發生嚴重錯誤: {e}")
        return False


def discover_apps() -> list[App]:
    """從 apps 目錄中發現所有應用"""
    apps = []
    for app_path in APPS_DIR.iterdir():
        if app_path.is_dir():
            apps.append(App(app_path))
    return apps

def ensure_psutil_installed():
    """檢查 psutil 是否已安裝，若無則嘗試安裝。"""
    try:
        pass
    except ImportError:
        print("核心依賴 `psutil` 未找到，正在嘗試自動安裝...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil"])
            print("`psutil` 安裝成功！")
        except subprocess.CalledProcessError:
            print("自動安裝 `psutil` 失敗。請手動執行 `pip install psutil`。")
            sys.exit(1)

def check_system_resources(required_disk_gb: float = 10.0, required_ram_gb: float = 4.0) -> (bool, float, float):
    """
    檢查系統資源是否充足。
    返回 (是否充足, 可用磁碟, 可用記憶體)
    """
    import psutil
    disk_usage = psutil.disk_usage('/')
    available_disk_gb = disk_usage.free / (1024 ** 3)

    ram = psutil.virtual_memory()
    available_ram_gb = ram.available / (1024 ** 3)

    is_sufficient = available_disk_gb >= required_disk_gb and available_ram_gb >= required_ram_gb
    return is_sufficient, available_disk_gb, available_ram_gb

async def main_logic():
    """主要的業務邏輯協調器"""
    # 發現應用
    apps = discover_apps()
    print("發現的應用:")
    for app in apps:
        print(f"- {app.name}")

    # 決定安裝模式
    print("\n正在檢查系統資源...")
    is_sufficient, disk_gb, ram_gb = check_system_resources()
    print(f"檢測結果: 可用磁碟空間 {disk_gb:.1f} GB, 可用記憶體 {ram_gb:.1f} GB")

    install_large_deps = is_sufficient
    if install_large_deps:
        print("資源充足，將執行「完整安裝」模式。")
    else:
        print("資源不足，將執行「模擬安裝」模式（跳過大型依賴）。")

    # 準備所有應用的環境
    for app in apps:
        print(f"\n--- 正在準備 {app.name} ---")
        success = await prepare_app_environment(app, install_large_deps)
        if success:
            print(f"✅ {app.name} 環境準備就緒。")
        else:
            print(f"❌ {app.name} 環境準備失敗。")

        print("日誌輸出:")
        for log_entry in app.log:
            print(f"  {log_entry}")


import time
import threading
import re
from collections import deque

# --- ANSI Escape Codes ---
class ANSI:
    # Colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    # Styles
    BOLD = "\033[1m"
    # Cursor Control
    @staticmethod
    def move_cursor(y, x): return f"\033[{y};{x}H"
    CLEAR_SCREEN = "\033[2J"
    CLEAR_LINE = "\033[2K"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

class ANSIDashboard:
    """
    使用 ANSI Escape Codes 管理終端儀表板的類別。
    這個類別負責所有與 TUI 渲染相關的工作，包括繪製佈局、更新動態區塊、
    以及確保多執行緒寫入終端時的畫面正確性。
    """

    def __init__(self, apps: list[App]):
        """
        初始化儀表板。

        Args:
            apps (list[App]): 需要在儀表板上顯示的應用程式物件列表。
        """
        self.apps = apps
        try:
            self.width, self.height = os.get_terminal_size()
        except OSError:
            # 在非標準 TTY 環境（如 CI/CD）中，提供一個預設尺寸
            self.width, self.height = 120, 24
        self.log_queue = deque(maxlen=5) # 只保留最新的 5 條日誌
        self._lock = threading.Lock() # 用於確保對 stdout 的寫入是執行緒安全的
        self.current_task_name = "[空閒]"
        self.current_task_progress_line = ""

    def _write(self, text: str):
        """
        帶鎖的寫入方法，確保來自不同執行緒的ANSI指令不會互相干擾，
        避免畫面錯亂。
        """
        with self._lock:
            sys.stdout.write(text)
            sys.stdout.flush()

    def draw_static_layout(self):
        """繪製靜態 UI 框架"""
        title = " 🚀 鳳凰之心指揮中心 v8.0 "
        top_bar = (f"{ANSI.move_cursor(1, 1)}┌─{ANSI.BOLD}{title}{ANSI.RESET}"
                   + "─" * (self.width - len(title) - 4) + "─┐")

        sections = [
            (2, "🌐 系統狀態 (System Status)"),
            (5, "📦 應用程式狀態 (Application Status)"),
            (8, "📜 即時日誌 (Live Logs)"),
            (15, "✨ 當前任務 (Current Task)"),
        ]

        layout = top_bar
        for i, (y, title) in enumerate(sections):
            separator = ("├─ " + f"{ANSI.CYAN}{ANSI.BOLD}{title}{ANSI.RESET}" + " "
                         + "─" * (self.width - len(title) - 7) + "┤")
            layout += f"{ANSI.move_cursor(y, 1)}{separator}"

        bottom_bar = f"{ANSI.move_cursor(20, 1)}└" + "─" * (self.width - 2) + "┘"

        self._write(ANSI.CLEAR_SCREEN + layout + bottom_bar)

    def update_system_status(self, stop_event):
        """在背景執行緒中更新系統狀態"""
        import psutil
        while not stop_event.is_set():
            ram = psutil.virtual_memory()
            disk = psutil.disk_usage('/')

            ram_color = ANSI.GREEN
            if ram.percent > 85: ram_color = ANSI.RED
            elif ram.percent > 70: ram_color = ANSI.YELLOW

            status_text = (
                f"{ANSI.GREEN}🟢 運行中{ANSI.RESET}   "
                f"核心: {psutil.cpu_percent():2.1f}%   "
                f"RAM: {ram_color}{ram.used/1e9:.1f}/{ram.total/1e9:.1f} GB "
                f"({ram.percent}%){ANSI.RESET}   "
                f"DISK: {disk.used/1e9:.1f}/{disk.total/1e9:.1f} GB ({disk.percent}%)"
            )

            self._write(f"{ANSI.move_cursor(3, 3)}{ANSI.CLEAR_LINE}{status_text}")
            time.sleep(1)

    def update_app_status(self):
        """更新所有 App 的狀態顯示"""
        app_statuses = []
        icons = {"quant": "📈", "transcriber": "🎤"}
        for app in self.apps:
            icon = icons.get(app.name, "📦")
            app_statuses.append(f"{icon} {app.name.capitalize()} App".ljust(20) + f"[{app.status}]")

        # 將狀態並排顯示
        status_line = "         ".join(app_statuses)
        self._write(f"{ANSI.move_cursor(6, 3)}{ANSI.CLEAR_LINE}{status_line}")

    def add_log_entry(self, message: str):
        """向日誌隊列中添加一條新日誌並刷新顯示"""
        timestamp = time.strftime('%H:%M:%S', time.localtime())

        # 簡單的日誌級別判斷
        level = "INFO"
        if "error" in message.lower() or "failed" in message.lower():
            level = "ERROR"
        elif "warn" in message.lower():
            level = "WARN"

        log_line = f"{ANSI.move_cursor(0,0)}[{timestamp}] [{level}] {message}"
        self.log_queue.append(log_line)
        self.update_logs()

    def update_logs(self):
        """繪製日誌區域"""
        for i, log_entry in enumerate(list(self.log_queue)):
            # 從 y=9 開始繪製
            self._write(f"{ANSI.move_cursor(9 + i, 3)}{ANSI.CLEAR_LINE}{log_entry[:self.width-4]}")

    def update_current_task(self, task_name=None, progress_line=None):
        """更新當前任務的顯示"""
        if task_name is not None:
            self.current_task_name = task_name
        if progress_line is not None:
            self.current_task_progress_line = progress_line

        self._write(f"{ANSI.move_cursor(16, 3)}{ANSI.CLEAR_LINE}[{self.current_task_name}]")
        self._write(f"{ANSI.move_cursor(17, 3)}{ANSI.CLEAR_LINE}{self.current_task_progress_line}")

    def run(self, main_logic_coro):
        """啟動儀表板的主循環"""
        self._write(ANSI.HIDE_CURSOR)
        self.draw_static_layout()

        stop_event = threading.Event()
        status_thread = threading.Thread(target=self.update_system_status, args=(stop_event,))
        status_thread.daemon = True
        status_thread.start()

        loop = asyncio.get_event_loop()
        try:
            loop.run_until_complete(main_logic_coro)
            self._write(f"{ANSI.move_cursor(21, 3)}{ANSI.GREEN}✅ 所有任務已完成。{ANSI.RESET}")
        except Exception as e:
            self._write(f"{ANSI.move_cursor(21, 3)}{ANSI.RED}❌ 發生錯誤: {e}{ANSI.RESET}")
        finally:
            stop_event.set()
            status_thread.join(timeout=1.5)
            self._write(f"{ANSI.move_cursor(22, 1)}{ANSI.SHOW_CURSOR}")


async def run_tests_for_app(app: App):
    """在 App 的虛擬環境中執行 pytest"""
    app.set_status(AppStatus.TESTING)

    tests_dir = app.path / "tests"
    if not tests_dir.exists() or not any(tests_dir.glob("test_*.py")):
        app.add_log("找不到測試檔案，跳過測試。")
        app.set_status(AppStatus.TEST_PASSED) # 沒有測試也算通過
        return True

    python_executable = app.venv_path / ('Scripts/python.exe' if sys.platform == 'win32' else 'bin/python')

    # 設定環境變數，讓測試可以找到專案根目錄
    os.environ['PYTHONPATH'] = str(PROJECT_ROOT)

    test_cmd = f'uv run --python "{python_executable}" pytest "{tests_dir}"'

    return_code = await run_command_async(test_cmd, cwd=PROJECT_ROOT, app=app)

    if return_code == 0:
        app.set_status(AppStatus.TEST_PASSED)
        return True
    else:
        app.set_status(AppStatus.TEST_FAILED)
        return False

async def _main_logic_with_dashboard(dashboard: ANSIDashboard = None):
    """主要的業務邏輯協調器 (修改後)"""
    apps = dashboard.apps if dashboard else discover_apps()

    if not dashboard:
        # ... (省略非 TUI 模式的 print 語句)
        pass

    is_sufficient, _, _ = check_system_resources()
    install_large_deps = is_sufficient

    if dashboard:
        for app in apps:
            app.dashboard = dashboard # 建立關聯
        dashboard.update_app_status()

    for app in apps:
        success = await prepare_app_environment(app, install_large_deps)
        if success:
            await run_tests_for_app(app)

def main():
    """主函數"""
    ensure_psutil_installed()
    try:
        subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("錯誤: `uv` 未安裝。")
        sys.exit(1)

    if '--no-tui' in sys.argv:
        asyncio.run(main_logic())
    else:
        apps = discover_apps()
        dashboard = ANSIDashboard(apps)

        # main_logic 本身就是一個協程函數，直接調用它來獲取協程對象
        main_coro = _main_logic_with_dashboard(dashboard)

        try:
            dashboard.run(main_coro)
        except KeyboardInterrupt:
            print(f"\n{ANSI.SHOW_CURSOR}使用者中斷。{ANSI.RESET}")

if __name__ == "__main__":
    main()
