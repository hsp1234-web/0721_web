import os
import sys
import subprocess
import threading
from pathlib import Path
import time
import shutil

# --- 模擬環境設定 ---
LAUNCHER_FILE = "colab_launcher_v15.py"
MOCK_CONTENT_DIR = Path.cwd() / "mock_content"
PROJECT_DIR = MOCK_CONTENT_DIR / "WEB1"

def setup_simulation_environment():
    """建立一個模擬的 Colab 環境"""
    print("--- Setting up v15 Simulation Environment ---")

    # 1. 建立資料夾結構
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # 2. 建立假的 requirements.txt (包含 FastAPI/Uvicorn)
    (PROJECT_DIR / "requirements.txt").write_text("psutil\npytz\nIPython\nfastapi\nuvicorn\npython-multipart")

    # 3. 建立一個更逼真的 main.py (FastAPI Server)
    (PROJECT_DIR / "main.py").write_text("""
import uvicorn
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"Hello": "World"}

if __name__ == "__main__":
    # uvicorn 會自己印出 "Uvicorn running on..."
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
""")
    # 4. 複製真實的 colab_run.py
    (PROJECT_DIR / "scripts").mkdir(exist_ok=True)
    os.system(f"cp scripts/colab_run.py {PROJECT_DIR / 'scripts'}")

    # 5. 建立一個假的 google.colab 模組來模擬 URL 獲取
    class FakeColabOutput:
        def eval_js(self, code):
            print(f"[SIMULATOR] google.colab.output.eval_js called.")
            return "https://abcdef-1234.colab.googleusercontent.com/"

    class FakeGoogle:
        class colab:
            output = FakeColabOutput()

    sys.modules['google'] = FakeGoogle
    sys.modules['google.colab'] = FakeGoogle.colab
    sys.modules['google.colab.output'] = FakeGoogle.colab.output

    print("--- v15 Simulation Environment is Ready ---")


def run_v15_simulation():
    """執行 v15 的模擬測試"""
    print("\n--- Running v15 Simulation Test ---")

    # 模擬 git clone, 我們手動建立檔案，所以讓啟動器跳過這一步
    # 我們透過修改 FORCE_REPO_REFRESH=False 和預先建立資料夾來實現
    # 這裡需要修改 launcher 的內容，但為了不污染原始檔案，我們建立一個臨時的測試版

    with open(LAUNCHER_FILE, "r") as f:
        launcher_code = f.read()

    # 讓啟動器在我們的模擬環境下運行
    test_launcher_code = launcher_code.replace(
        'base_path = Path("/content")',
        f'base_path = Path("{MOCK_CONTENT_DIR}")'
    ).replace(
        'FORCE_REPO_REFRESH = True',
        'FORCE_REPO_REFRESH = False' # 跳過 git clone
    )

    test_launcher_file = "test_launcher.py"
    with open(test_launcher_file, "w") as f:
        f.write(test_launcher_code)

    process = subprocess.Popen(
        [sys.executable, test_launcher_file],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8'
    )

    output_lines = []
    success = False

    def reader_thread(pipe):
        for line in iter(pipe.readline, ''):
            print(line, end='')
            output_lines.append(line)

    thread = threading.Thread(target=reader_thread, args=(process.stdout,))
    thread.start()

    # 等待子程序結束，超時時間應該比 launcher 自己的超時長一點
    try:
        process.wait(timeout=100)
    except subprocess.TimeoutExpired:
        print("\n[SIMULATOR] Main process timeout. This is unexpected. Terminating.")
        process.terminate()

    thread.join()

    # 最終檢查
    output_text = "".join(output_lines)
    if "伺服器 URL 已成功獲取" in output_text and "https://" in output_text:
        success = True

    print("\n" + "="*40)
    print("--- v15 Simulation Test Finished ---")
    if success:
        print("✅✅✅ v15 Simulation PASSED! Server started and URL was retrieved.")
    else:
        print("❌❌❌ v15 Simulation FAILED.")
        print("\n--- Full Log ---")
        print(output_text)
    print("="*40)

    return success

def cleanup():
    """清理模擬環境"""
    print("\n--- Cleaning up ---")
    if MOCK_CONTENT_DIR.exists():
        shutil.rmtree(MOCK_CONTENT_DIR)
    if os.path.exists("test_launcher.py"):
        os.remove("test_launcher.py")
    print("✅ Cleanup complete.")

if __name__ == "__main__":
    try:
        setup_simulation_environment()
        run_v15_simulation()
    finally:
        cleanup()
