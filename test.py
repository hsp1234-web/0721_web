import subprocess
import time
import os
import sys
import httpx
import psutil
import threading
from pathlib import Path

# --- 常數與設定 ---
PROJECT_ROOT = Path(__file__).resolve().parent
DASHBOARD_URL = "http://localhost:8080"
QUANT_API_URL = "http://localhost:8001"
TRANSCRIBER_API_URL = "http://localhost:8002"
MAX_WAIT_TIME = 60  # 秒

# --- 輔助函式 ---

def print_header(title):
    """印出帶有邊框的標題"""
    print("\n" + "="*70)
    print(f"===== {title.center(60)} =====")
    print("="*70)

def print_success(message):
    print(f"✅ {message}")

def print_failure(message):
    print(f"❌ {message}")

def print_info(message):
    print(f"ℹ️ {message}")

def start_process(command, log_file):
    """在背景啟動一個進程並將其輸出記錄到檔案"""
    print_info(f"正在啟動: {' '.join(command)}")
    with open(log_file, "w") as f:
        process = subprocess.Popen(
            command,
            stdout=f,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8'
        )
    print_success(f"進程已啟動 (PID: {process.pid})，日誌位於: {log_file}")
    return process

def check_service_health(url, service_name):
    """檢查一個服務是否已啟動並回應"""
    print_info(f"正在檢查 {service_name} ({url}) 的健康狀態...")
    start_time = time.time()
    while time.time() - start_time < MAX_WAIT_TIME:
        try:
            response = httpx.get(url, timeout=5)
            if response.status_code == 200:
                print_success(f"{service_name} 已就緒！")
                return True
        except httpx.RequestError:
            time.sleep(2)
    print_failure(f"{service_name} 在 {MAX_WAIT_TIME} 秒內未能啟動。")
    return False

class SystemTest:
    def __init__(self):
        self.processes = []

    def run_static_analysis(self):
        print_header("靜態程式碼分析 (Ruff)")
        try:
            subprocess.check_call([
                "ruff", "check", ".", "--select", "F", "--exclude", "ALL_DATE",
                "--exclude", "run/colab_run_v2.py",
                "--exclude", "run/colab_run_v3.py",
                "--exclude", "run/colab_run_v5.py",
                "--exclude", "colab_launcher.py"
            ])
            print_success("Ruff 檢查通過，未發現語法錯誤。")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print_failure("Ruff 檢查發現錯誤或未安裝 Ruff。請檢查上面的日誌。")
            raise

    def setup(self):
        self.run_static_analysis()
        print_header("環境準備與啟動 (Setup)")
        # 啟動儀表板
        dashboard_process = start_process(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "launch.py"), "--dashboard"],
            "dashboard_test.log"
        )
        self.processes.append(dashboard_process)
        if not check_service_health(DASHBOARD_URL, "儀表板 (GoTTY)"):
            raise RuntimeError("儀表板啟動失敗")

        # 這裡可以加入解析日誌的邏輯來確認 App 狀態
        print_info("儀表板已啟動，假設內部 App 測試已通過 (進階測試可解析日誌)")

        # 關閉儀表板並啟動後端服務
        self.teardown()

        print_info("正在啟動後端 API 服務...")
        api_process = start_process(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "launch.py")],
            "api_test.log"
        )
        self.processes.append(api_process)
        if not check_service_health(f"{QUANT_API_URL}/docs", "Quant App API"):
            raise RuntimeError("Quant App API 啟動失敗")
        if not check_service_health(f"{TRANSCRIBER_API_URL}/docs", "Transcriber App API"):
            raise RuntimeError("Transcriber App API 啟動失敗")

    def test_quant_app(self):
        print_header("功能性測試: Quant App")
        # 假設的 API 端點和請求
        # 由於目前沒有實際的 backtest 端點，我們先測試 /docs
        response = httpx.get(f"{QUANT_API_URL}/docs")
        assert response.status_code == 200
        print_success("Quant App /docs 端點測試通過")

    def test_transcriber_app(self):
        print_header("功能性測試: Transcriber App")
        # 建立一個假的 wav 檔案
        test_wav_path = PROJECT_ROOT / "test_audio.wav"
        with open(test_wav_path, "wb") as f:
            f.write(b'RIFF\x00\x00\x00\x00WAVEfmt \x10\x00\x00\x00\x01\x00\x01\x00\x80\xbb\x00\x00\x00\xee\x02\x00\x02\x00\x10\x00data\x00\x00\x00\x00')

        # 假設的 API 端點和請求
        # 由於目前沒有實際的 transcribe 端點，我們先測試 /docs
        response = httpx.get(f"{TRANSCRIBER_API_URL}/docs")
        assert response.status_code == 200
        print_success("Transcriber App /docs 端點測試通過")

        # 清理測試檔案
        os.remove(test_wav_path)

    def test_memory_pressure(self):
        print_header("資源壓力測試: 記憶體")

        def eat_memory():
            print_info("記憶體壓力測試子進程啟動，將在 10 秒後結束。")
            a = []
            while psutil.virtual_memory().percent < 70:
                a.append(' ' * 10**6) # 每次分配 1MB
                time.sleep(0.1)
            print_info("記憶體使用率已超過 70%。")

        # 在一個單獨的執行緒中執行記憶體壓力測試
        pressure_thread = threading.Thread(target=eat_memory)
        pressure_thread.start()
        pressure_thread.join(timeout=20) # 最多執行 20 秒

        if psutil.virtual_memory().percent >= 70:
            print_success("成功模擬記憶體壓力超過 70%")
        else:
            print_failure("未能在指定時間內達到 70% 記憶體壓力")

        # 這裡可以加入檢查系統反應的邏輯

    def test_disk_pressure(self):
        print_header("資源壓力測試: 磁碟")
        large_file = PROJECT_ROOT / "large_test_file"

        # 建立一個 1GB 的大檔案
        print_info("正在建立一個 1GB 的大型檔案來模擬磁碟壓力...")
        with open(large_file, "wb") as f:
            f.seek(1024 * 1024 * 1024 - 1)
            f.write(b'\0')

        print_success("大型檔案已建立。")

        # 這裡可以加入檢查系統反應的邏輯

        # 清理
        os.remove(large_file)
        print_info("大型檔案已刪除。")

    def teardown(self):
        print_header("清理 (Teardown)")
        for p in self.processes:
            if p.poll() is None:
                print_info(f"正在終止進程 PID: {p.pid}")
                p.terminate()
                try:
                    p.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    print_failure(f"PID {p.pid} 未能終止，強制結束。")
                    p.kill()
        self.processes = []
        print_success("所有測試進程已關閉。")

    def run_all_tests(self):
        try:
            self.setup()
            self.test_quant_app()
            self.test_transcriber_app()
            self.test_memory_pressure()
            self.test_disk_pressure()
        except Exception as e:
            print_failure(f"測試過程中發生錯誤: {e}")
        finally:
            self.teardown()
            print_header("所有測試已完成")

if __name__ == "__main__":
    tester = SystemTest()
    tester.run_all_tests()
