import os
import sys
import subprocess
from pathlib import Path
import threading

# --- 模擬環境設定 ---
# 在當前目錄下模擬 Colab 的 /content 資料夾，以避免權限問題
CONTENT_DIR = Path.cwd() / "mock_content"
PROJECT_DIR = CONTENT_DIR / "WEB1"
SCRIPTS_DIR = PROJECT_DIR / "scripts"
FAKE_GIT_SCRIPT = "fake_git.py"
FAKE_MAIN_PY = PROJECT_DIR / "main.py"
FAKE_REQUIREMENTS_TXT = PROJECT_DIR / "requirements.txt"
COLAB_LAUNCHER = "colab_v10_fixed.py"

# --- 模擬 Colab 的 IPython.display ---
class FakeIPython:
    class display:
        def clear_output(self, wait=False):
            print("[SIMULATOR] IPython.display.clear_output() called.")

sys.modules['IPython'] = FakeIPython
sys.modules['IPython.display'] = FakeIPython.display
sys.modules['google.colab'] = "dummy" # 避免 colab_run.py 匯入失敗

def setup_simulation_environment():
    """建立一個完整的、模擬的 Colab 環境"""
    print("--- Setting up Simulation Environment ---")

    # 1. 建立資料夾結構
    CONTENT_DIR.mkdir(exist_ok=True)
    # 不建立 PROJECT_DIR，讓啟動器自己 clone

    # 2. 建立一個假的 git clone 腳本
    #    這個腳本會建立專案資料夾，並在裡面放入必要的檔案
    with open(FAKE_GIT_SCRIPT, "w", encoding="utf-8") as f:
        f.write("""
import os
from pathlib import Path
import sys

print("Fake git clone is running...")
project_dir = Path(sys.argv[-1])
scripts_dir = project_dir / "scripts"
scripts_dir.mkdir(parents=True, exist_ok=True)

# 建立假的 requirements.txt
with open(project_dir / "requirements.txt", "w") as req:
    req.write("faker\\n") # 寫入一個輕量級的套件

# 建立假的 main.py (FastAPI Server)
with open(project_dir / "main.py", "w") as main:
    main.write('''
import time
print("Uvicorn running on http://0.0.0.0:8000")
time.sleep(10) # 模擬伺服器運行
''')

# 複製真實的 colab_run.py 到模擬的 scripts 資料夾
os.system(f"cp scripts/colab_run.py {scripts_dir}")
print(f"Fake git has 'cloned' the repo into {project_dir}")
""")

    # 3. 將 fake_git.py 加入到 PATH
    os.environ["PATH"] = f"{os.getcwd()}:{os.environ['PATH']}"
    os.chmod(FAKE_GIT_SCRIPT, 0o755)

    # 4. 建立一個假的 google.colab.output.eval_js
    #    這是最棘手的部分，因為它在背景執行緒中被呼叫
    def fake_eval_js(code):
        print("[SIMULATOR] google.colab.output.eval_js called with: {code}")
        return "https://abcdef-1234.colab.googleusercontent.com/"

    try:
        from google.colab import output as colab_output
        colab_output.eval_js = fake_eval_js
    except Exception:
        # 如果 google.colab 模組結構複雜，我們需要更換策略
        class FakeColabOutput:
            def eval_js(self, code):
                return fake_eval_js(code)

        class FakeGoogle:
            class colab:
                output = FakeColabOutput()

        sys.modules['google.colab'] = FakeGoogle.colab
        sys.modules['google.colab.output'] = FakeGoogle.colab.output

    print("--- Simulation Environment is Ready ---")


def run_simulation():
    """執行模擬測試"""
    print("\n--- Running Simulation Test ---")

    # 設定環境變數
    env = os.environ.copy()
    env["GIT_PYTHON_GIT_EXECUTABLE"] = f"./{FAKE_GIT_SCRIPT}"
    env["SIMULATION_MODE"] = "true"

    # 使用 Popen 以非阻塞方式讀取輸出
    process = subprocess.Popen(
        [sys.executable, COLAB_LAUNCHER],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        env=env
    )

    output_lines = []
    success = False

    # 異步讀取輸出
    def reader_thread(pipe):
        for line in iter(pipe.readline, ''):
            print(line, end='')
            output_lines.append(line)

    thread = threading.Thread(target=reader_thread, args=(process.stdout,))
    thread.start()

    try:
        process.wait(timeout=30) # 給予 30 秒的執行時間
    except subprocess.TimeoutExpired:
        print("\n[SIMULATOR] Timeout reached. Terminating process.")
        process.terminate()

    thread.join()

    # 檢查結果
    output_text = "".join(output_lines)
    if "FastAPI 伺服器已成功啟動！" in output_text and "網頁介面 URL 已成功獲取" in output_text:
        success = True

    print("\n--- Simulation Test Finished ---")
    if success:
        print("✅ Simulation PASSED!")
    else:
        print("❌ Simulation FAILED. Server did not start as expected.")
        # 顯示完整 log 以便除錯
        print("\n--- Full Log ---")
        print(output_text)


def cleanup():
    """清理模擬環境"""
    print("\n--- Cleaning up ---")
    if CONTENT_DIR.exists():
        subprocess.run(["sudo", "rm", "-rf", str(CONTENT_DIR)], check=True)
    if os.path.exists(FAKE_GIT_SCRIPT):
        os.remove(FAKE_GIT_SCRIPT)
    print("✅ Cleanup complete.")


if __name__ == "__main__":
    try:
        setup_simulation_environment()
        run_simulation()
    finally:
        cleanup()
