import os
import sys
import subprocess
import threading
from pathlib import Path
import time
import shutil

# --- 模擬環境設定 ---
LAUNCHER_FILE = "colab_launcher_v16_integrated.py"
MOCK_CONTENT_DIR = Path.cwd() / "mock_content"

def setup_simulation_environment():
    """為了 v16 啟動器，我們只需要偽造 Colab 的模組即可。"""
    print("--- Setting up v16 Simulation Environment ---")

    # 偽造 Colab 的模組
    class FakeDisplay:
        def clear_output(self, wait=False):
            # 在終端中，我們用 ANSI escape code 來模擬清屏
            print("\033[H\033[J", end="")

    class FakeColabOutput:
        def eval_js(self, code):
            print(f"[SIMULATOR] google.colab.output.eval_js called.")
            return "https://abcdef-1234.colab.googleusercontent.com/"

    class FakeGoogle:
        class colab:
            output = FakeColabOutput()

    # 將偽造的模組注入 sys.modules
    sys.modules['IPython'] = FakeDisplay
    sys.modules['IPython.display'] = FakeDisplay()
    sys.modules['google'] = FakeGoogle
    sys.modules['google.colab'] = FakeGoogle.colab
    sys.modules['google.colab.output'] = FakeGoogle.colab.output

    print("--- v16 Simulation Environment is Ready ---")

def run_v16_simulation():
    """執行 v16 的模擬測試"""
    print("\n--- Running v16 Simulation Test ---")

    # 我們需要一個假的 main.py 和 requirements.txt
    # 這些會被 launcher 自己建立，因為它在模擬模式下會這樣做
    # 我們只需要傳遞環境變數即可
    env = os.environ.copy()
    env["SIMULATION_MODE"] = "true" # 觸發 launcher 中的模擬邏輯

    # 為了讓 launcher 能找到它自己，我們把它複製到一個臨時檔案
    with open(LAUNCHER_FILE, "r") as f:
        launcher_code = f.read()

    test_launcher_file = "test_launcher_v16.py"
    with open(test_launcher_file, "w") as f:
        f.write(launcher_code)

    process = subprocess.Popen(
        [sys.executable, test_launcher_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        env=env
    )

    output_lines = []
    success = False

    # 完整地讀取所有輸出
    for line in iter(process.stdout.readline, ''):
        print(line, end='')
        output_lines.append(line)

    process.wait()

    # 最終檢查
    output_text = "".join(output_lines)
    if "伺服器 URL 已成功獲取" in output_text and "https://" in output_text:
        success = True

    print("\n" + "="*40)
    print("--- v16 Simulation Test Finished ---")
    if success and process.returncode == 0:
        print("✅✅✅ v16 Simulation PASSED! Server started and URL was retrieved.")
    else:
        print(f"❌❌❌ v16 Simulation FAILED. Return code: {process.returncode}")
        print("\n--- Full Log ---")
        print(output_text)
    print("="*40)

    return success

def cleanup():
    """清理模擬環境"""
    print("\n--- Cleaning up ---")
    if MOCK_CONTENT_DIR.exists():
        shutil.rmtree(MOCK_CONTENT_DIR)
    if os.path.exists("test_launcher_v16.py"):
        os.remove("test_launcher_v16.py")
    print("✅ Cleanup complete.")

if __name__ == "__main__":
    # 在執行前，先確保環境是乾淨的
    cleanup()
    try:
        # 由於 v16 啟動器會自己安裝依賴，我們不需要在這裡偽造它們
        # 我們只需要偽造 Colab 特有的模組
        setup_simulation_environment()
        run_v16_simulation()
    finally:
        cleanup()
