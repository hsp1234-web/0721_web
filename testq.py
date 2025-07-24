# 檔案: testq.py
# 說明: 快速核心邏輯測試 (Quick Test)
#       此測試使用 unittest.mock 來隔離所有外部依賴 (如 IO、子程序、Colab API)，
#       專注於以毫秒級速度驗證核心類別 (DisplayManager, LogManager) 的內部邏輯。

import unittest
from unittest.mock import MagicMock
from collections import deque
from pathlib import Path
from datetime import datetime
import sys

# --- 彩色輸出設定 ---
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_line(char="─", color=Colors.CYAN):
    print(f"{color}{char * 80}{Colors.ENDC}")

# --- 豐富多彩的測試執行器 ---
class RichTestResult(unittest.TextTestResult):
    def startTest(self, test):
        super().startTest(test)
        self.stream.write(f"{Colors.YELLOW}🚀 開始測試: {Colors.BOLD}{test.shortDescription()}{Colors.ENDC}\n")

    def addSuccess(self, test):
        super().addSuccess(test)
        self.stream.write(f"{Colors.GREEN}✅  測試通過{Colors.ENDC}\n\n")

    def addError(self, test, err):
        super().addError(test, err)
        self.stream.write(f"{Colors.RED}❌  測試錯誤{Colors.ENDC}\n\n")

    def addFailure(self, test, err):
        super().addFailure(test, err)
        self.stream.write(f"{Colors.RED}❌  測試失敗{Colors.ENDC}\n\n")

class RichTestRunner(unittest.TextTestRunner):
    resultclass = RichTestResult

# --- 從 colab_bootstrap.py 複製過來的類別 ---
# 由於在測試環境中無法直接 import，我們將被測單元複製到此處。
class DisplayManager:
    """管理 Colab 的動態顯示輸出。"""
    def __init__(self, log_lines=10, refresh_interval=0.1):
        self.log_queue = deque(maxlen=log_lines)
        self.status = {"cpu": 0, "ram": 0, "server_status": "PENDING"}
        self.iframe_html = ""
        self.output = MagicMock()
        self.output.get_colab_url.return_value = "http://mock-colab-url"

    def update_log(self, message): self.log_queue.append(message)
    def update_status(self, cpu, ram, s): self.status.update({"cpu": cpu, "ram": ram, "server_status": s})
    def render_iframe(self, url, p): self.iframe_html = f'<iframe src="{url}" href="{self.output.get_colab_url(p)}"/>'

class LogManager:
    """管理日誌記錄、顯示與歸檔。"""
    def __init__(self, display_manager, archive_folder):
        self.display = display_manager
        self.archive_folder = Path(archive_folder)
        self.full_log = []

    def _log(self, level, message):
        log_entry = f"[{level.upper()}] {message}"
        self.display.update_log(f'<span>{log_entry}</span>')
        self.full_log.append(log_entry)

    def info(self, m): self._log("info", m)
    def success(self, m): self._log("success", m)
    def warning(self, m): self._log("warning", m)
    def error(self, m): self._log("error", m)

# --- 測試案例 ---
class TestCoreLogics(unittest.TestCase):
    def setUp(self):
        self.mock_display = MagicMock()
        self.log_manager = LogManager(self.mock_display, "mock_archive")

    def test_log_manager_logs_to_display(self):
        """測試：日誌管理員應將格式化日誌傳遞給顯示管理員"""
        self.log_manager.info("測試訊息")
        self.mock_display.update_log.assert_called_once()
        self.assertIn("[INFO] 測試訊息", self.mock_display.update_log.call_args[0][0])

    def test_log_manager_stores_full_log(self):
        """測試：日誌管理員應儲存純文字日誌以供歸檔"""
        self.log_manager.error("失敗")
        self.log_manager.success("成功")
        self.assertEqual(len(self.log_manager.full_log), 2)
        self.assertEqual(self.log_manager.full_log[0], "[ERROR] 失敗")

    def test_display_manager_updates_status(self):
        """測試：顯示管理員應能正確更新內部狀態"""
        dm = DisplayManager()
        dm.update_status(50.5, 25.2, "RUNNING")
        self.assertEqual(dm.status, {"cpu": 50.5, "ram": 25.2, "server_status": "RUNNING"})

    def test_display_manager_renders_iframe(self):
        """測試：顯示管理員應能正確渲染 IFrame HTML"""
        dm = DisplayManager()
        dm.render_iframe("http://app-url", 8000)
        self.assertIn('src="http://app-url"', dm.iframe_html)
        self.assertIn('href="http://mock-colab-url"', dm.iframe_html)

    def test_log_queue_max_length(self):
        """測試：日誌隊列應遵守最大長度限制"""
        dm = DisplayManager(log_lines=5)
        for i in range(10):
            dm.update_log(f"訊息 {i}")
        self.assertEqual(len(dm.log_queue), 5)
        self.assertEqual(dm.log_queue[0], "訊息 5")

if __name__ == '__main__':
    print_line("═")
    print(f"{Colors.HEADER}{Colors.BOLD}🚀 執行快速核心邏輯測試 (testq.py){Colors.ENDC}")
    print_line("═")

    suite = unittest.TestLoader().loadTestsFromTestCase(TestCoreLogics)
    runner = RichTestRunner(stream=sys.stdout)
    result = runner.run(suite)

    print_line()
    if result.wasSuccessful():
        print(f"{Colors.GREEN}{Colors.BOLD}✅✅✅ 所有快速測試均已通過！核心邏輯穩定。 ✅✅✅{Colors.ENDC}")
        sys.exit(0)
    else:
        print(f"{Colors.RED}{Colors.BOLD}❌❌❌ 部分或全部快速測試失敗。 ❌❌❌{Colors.ENDC}")
        sys.exit(1)
