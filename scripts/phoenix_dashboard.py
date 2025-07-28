# -*- coding: utf-8 -*-
"""
🚀 鳳凰之心指揮中心 (Phoenix Heart Command Center) 🚀

這是一個在 `gotty` 環境中運行的視覺化儀表板。
它的唯一職責是：
- 監控由 `launch.py` 啟動的後端微服務的狀態。
- 提供一個介面來觸發測試。
- 顯示系統的即時狀態。

此腳本不處理任何環境安裝或依賴管理。它假設 `launch.py` 已經
完成了所有準備工作。
"""
import asyncio
import os
import subprocess
import sys
import time
import threading
from pathlib import Path

import httpx  # 用於健康檢查

# --- 常數與設定 ---
PROJECT_ROOT = Path(__file__).resolve().parent.parent
APPS = {
    "quant": {"port": 8001, "status": "⚪ 待檢查...", "url": "http://localhost:8001"},
    "transcriber": {"port": 8002, "status": "⚪ 待檢查...", "url": "http://localhost:8002"},
}

# --- ANSI Escape Codes ---
class ANSI:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    @staticmethod
    def move_cursor(y, x): return f"\033[{y};{x}H"
    CLEAR_SCREEN = "\033[2J"
    CLEAR_LINE = "\033[2K"
    HIDE_CURSOR = "\033[?25l"
    SHOW_CURSOR = "\033[?25h"

class ANSIDashboard:
    """管理終端儀表板的類別"""

    def __init__(self):
        try:
            self.width, self.height = os.get_terminal_size()
        except OSError:
            self.width, self.height = 120, 24
        self.log_messages = []
        self._lock = threading.Lock()
        self.test_status = "⚪ 未執行"
        self.test_output = []

    def _write(self, text: str):
        with self._lock:
            sys.stdout.write(text)
            sys.stdout.flush()

    def draw_static_layout(self):
        """繪製靜態 UI 框架"""
        title = " 🚀 鳳凰之心指揮中心 "
        top_bar = f"{ANSI.move_cursor(1, 1)}┌─{ANSI.BOLD}{title}{ANSI.RESET}" + "─" * (self.width - len(title) - 4) + "─┐"

        sections = [
            (2, "📦 應用程式狀態 (Application Status)"),
            (6, "🧪 整合測試 (Integration Tests)"),
            (9, "📜 系統日誌 (System Logs)"),
        ]

        layout = top_bar
        for i, (y, title) in enumerate(sections):
            separator = "├─ " + f"{ANSI.CYAN}{ANSI.BOLD}{title}{ANSI.RESET}" + " " + "─" * (self.width - len(title) - 7) + "┤"
            layout += f"{ANSI.move_cursor(y, 1)}{separator}"

        bottom_bar = f"{ANSI.move_cursor(20, 1)}└" + "─" * (self.width - 2) + "┘"
        instructions = f"{ANSI.move_cursor(21, 3)}按 't' 執行測試, 按 'q' 退出"

        self._write(ANSI.CLEAR_SCREEN + layout + bottom_bar + instructions)

    def add_log(self, message):
        timestamp = time.strftime('%H:%M:%S')
        self.log_messages.insert(0, f"[{timestamp}] {message}")
        if len(self.log_messages) > 5:
            self.log_messages.pop()
        self.update_logs()

    def update_logs(self):
        for i, msg in enumerate(self.log_messages):
            self._write(f"{ANSI.move_cursor(10 + i, 3)}{ANSI.CLEAR_LINE}{msg[:self.width-4]}")

    def update_app_status(self):
        """更新所有 App 的狀態顯示"""
        status_line = ""
        icons = {"quant": "📈", "transcriber": "🎤"}
        for i, (name, config) in enumerate(APPS.items()):
            icon = icons.get(name, "📦")
            status_text = f"{icon} {name.capitalize()} App".ljust(20) + f"[{config['status']}]"
            status_line += status_text + "    "

        self._write(f"{ANSI.move_cursor(3, 3)}{ANSI.CLEAR_LINE}{status_line}")

    def update_test_status(self):
        self._write(f"{ANSI.move_cursor(7, 3)}{ANSI.CLEAR_LINE}狀態: {self.test_status}")
        if self.test_output:
            output_line = self.test_output[-1] # 只顯示最後一行
            self._write(f"{ANSI.move_cursor(8, 3)}{ANSI.CLEAR_LINE}輸出: {output_line[:self.width-10]}")

    async def run_health_checks(self, stop_event):
        """定期檢查服務健康狀況"""
        async with httpx.AsyncClient(timeout=5) as client:
            while not stop_event.is_set():
                for name, config in APPS.items():
                    try:
                        response = await client.get(f"{config['url']}/health")
                        if response.status_code == 200:
                            config["status"] = f"{ANSI.GREEN}✔ 在線{ANSI.RESET}"
                        else:
                            config["status"] = f"{ANSI.YELLOW}⚠ 異常 ({response.status_code}){ANSI.RESET}"
                    except httpx.RequestError:
                        config["status"] = f"{ANSI.RED}✖ 離線{ANSI.RESET}"

                self.update_app_status()
                await asyncio.sleep(5)

    def run_tests(self):
        """執行整合測試"""
        self.test_status = "🔄 測試中..."
        self.test_output = ["開始執行測試..."]
        self.update_test_status()
        self.add_log("使用者觸發了整合測試。")

        try:
            process = subprocess.Popen(
                ["bash", str(PROJECT_ROOT / "scripts" / "run_tests.sh")],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8'
            )
            for line in iter(process.stdout.readline, ''):
                self.test_output.append(line.strip())
                self.update_test_status()

            process.wait()
            if process.returncode == 0:
                self.test_status = f"{ANSI.GREEN}✔ 測試通過{ANSI.RESET}"
            else:
                self.test_status = f"{ANSI.RED}✖ 測試失敗 (Code: {process.returncode}){ANSI.RESET}"

            self.add_log(f"測試完成，狀態: {self.test_status}")

        except Exception as e:
            self.test_status = f"{ANSI.RED}✖ 執行錯誤{ANSI.RESET}"
            self.test_output.append(str(e))
            self.add_log(f"執行測試時發生錯誤: {e}")

        self.update_test_status()

    def handle_input(self, stop_event):
        """處理使用者輸入"""
        # 讓終端進入非緩衝模式
        import termios, tty
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setcbreak(sys.stdin.fileno())
            while not stop_event.is_set():
                if sys.stdin.read(1) == 't':
                    # 在單獨的執行緒中運行測試，避免阻塞UI
                    threading.Thread(target=self.run_tests, daemon=True).start()
                elif sys.stdin.read(1) == 'q':
                    stop_event.set()
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


    async def run(self):
        """啟動儀表板的主循環"""
        self._write(ANSI.HIDE_CURSOR)
        self.draw_static_layout()
        self.add_log("儀表板已啟動。正在監控服務...")
        self.update_app_status()
        self.update_test_status()

        stop_event = asyncio.Event()

        # 啟動背景健康檢查
        health_check_task = asyncio.create_task(self.run_health_checks(stop_event))

        # 啟動輸入處理
        input_thread = threading.Thread(target=self.handle_input, args=(stop_event,), daemon=True)
        input_thread.start()

        await stop_event.wait()

        health_check_task.cancel()
        self._write(f"{ANSI.move_cursor(22, 1)}{ANSI.SHOW_CURSOR}儀表板正在關閉...")


def main():
    # 檢查是否在 gotty 環境中
    if not os.environ.get("GOTTY_SERVER_VERSION"):
        print("錯誤: 此腳本應在 `gotty` 環境中運行。")
        print("請使用 `python scripts/launch.py --dashboard` 啟動。")
        sys.exit(1)

    dashboard = ANSIDashboard()
    try:
        asyncio.run(dashboard.run())
    except KeyboardInterrupt:
        print("\n使用者中斷。")
    finally:
        print(f"{ANSI.SHOW_CURSOR}{ANSI.RESET}")

if __name__ == "__main__":
    main()
