import os
import sys
import subprocess
import threading
from pathlib import Path

LAUNCHER_FILE = "colab_ultimate_launcher.py"

def run_final_simulation():
    """
    執行最終的、簡化的模擬測試。
    """
    print("--- Running Final Simulation Test ---")

    # 設定環境變數
    env = os.environ.copy()
    env["SIMULATION_MODE"] = "true"

    process = subprocess.Popen(
        [sys.executable, LAUNCHER_FILE],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding='utf-8',
        env=env
    )

    output_lines = []
    success = False

    # 異步讀取輸出，避免阻塞
    def reader_thread(pipe):
        for line in iter(pipe.readline, ''):
            print(line, end='')
            output_lines.append(line)
            # 可以在這裡加入即時檢查
            if "網頁介面 URL:" in line:
                # 為了讓主執行緒知道，可以設定一個 event
                pass

    thread = threading.Thread(target=reader_thread, args=(process.stdout,))
    thread.start()

    try:
        # 等待子程序結束，設定一個合理的超時
        process.wait(timeout=20)
    except subprocess.TimeoutExpired:
        print("\n[SIMULATOR] Timeout reached as expected. Terminating process.")
        process.terminate()

    thread.join()

    # 最終檢查
    output_text = "".join(output_lines)
    if "FastAPI 伺服器已成功啟動！" in output_text and "網頁介面 URL:" in output_text:
        success = True

    print("\n" + "="*40)
    print("--- Final Simulation Test Finished ---")
    if success:
        print("✅✅✅ Simulation PASSED! The server started successfully.")
    else:
        print("❌❌❌ Simulation FAILED. Server did not start as expected.")
        print("\n--- Full Log ---")
        print(output_text)
    print("="*40)

    # 清理模擬資料夾
    mock_content_dir = Path.cwd() / "mock_content"
    if mock_content_dir.exists():
        subprocess.run(["sudo", "rm", "-rf", str(mock_content_dir)], check=True)
        print("✅ Mock content directory cleaned up.")

    return success

if __name__ == "__main__":
    run_final_simulation()
