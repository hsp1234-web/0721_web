# 檔案: teste2e.py
# 說明: 端到端整合測試 (End-to-End Test)
#       此測試模擬在 Colab 環境中執行 `colab_run.py` 的完整流程。
#       它將整個應用程式視為一個黑盒子，透過監控其輸出來驗證功能。
#       它的執行時間較長，但提供了最高的整合信心。

import subprocess
import sys
import time
import shutil
from pathlib import Path
import os
import signal

# --- 常數設定 ---
SIMULATION_TIMEOUT = 60  # 秒，給予安裝依賴和啟動伺服器的完整時間
SHUTDOWN_WAIT_TIMEOUT = 15 # 秒，等待優雅關閉的時間
ARCHIVE_FOLDER_NAME = "作戰日誌歸檔"

def print_test_step(message: str):
    """打印格式化的測試步驟標題。"""
    print(f"\n{'='*70}")
    print(f"🛰️  {message}")
    print(f"{'='*70}")

def cleanup_previous_run():
    """清理上一次測試可能留下的產物。"""
    print_test_step("清理環境")
    # 清理日誌歸檔
    archive_dir = Path(ARCHIVE_FOLDER_NAME)
    if archive_dir.exists():
        print(f"INFO: 正在刪除已存在的歸檔目錄: {archive_dir}")
        shutil.rmtree(archive_dir)
    # 清理 venv
    venv_dir = Path(".venv")
    if venv_dir.exists():
        print(f"INFO: 正在刪除已存在的虛擬環境: {venv_dir}")
        shutil.rmtree(venv_dir)
    # 清理模擬模組 (如果存在)
    mocks_dir = Path("mocks")
    if mocks_dir.exists():
        print(f"INFO: 正在刪除已存在的模擬模組目錄: {mocks_dir}")
        shutil.rmtree(mocks_dir)
    print("✅ 清理完畢。")

def main():
    """主測試函式。"""
    cleanup_previous_run()

    # --- 步驟 1: 建立虛擬環境和模擬模組 ---
    # 這是為了解決 `colab_bootstrap.py` 的匯入問題所必需的準備工作
    print_test_step("準備測試環境 (venv & mocks)")
    try:
        subprocess.run(["python3", "-m", "venv", ".venv"], check=True)
        # 我們需要模擬 google.colab 和 IPython
        os.makedirs("mocks/google/colab", exist_ok=True)
        os.makedirs("mocks/IPython", exist_ok=True)
        Path("mocks/__init__.py").touch()
        Path("mocks/google/__init__.py").touch()
        Path("mocks/google/colab/__init__.py").touch()
        Path("mocks/IPython/__init__.py").touch()
        with open("mocks/google/colab/output.py", "w") as f:
            f.write('def get_colab_url(port, **kwargs): return f"http://mock-url:{port}"\n')
            f.write('def display(*args, **kwargs): pass\n')
            f.write('def update_display(*args, **kwargs): pass\n')
            f.write('def HTML(s): return s\n')
        with open("mocks/IPython/display.py", "w") as f:
            f.write('def display(*args, **kwargs): pass\n')
            f.write('def update_display(*args, **kwargs): pass\n')
            f.write('def HTML(s): return s\n')
        print("✅ 虛擬環境和模擬模組已建立。")
    except Exception as e:
        print(f"❌ 致命錯誤: 準備環境時失敗: {e}", file=sys.stderr)
        sys.exit(1)


    # --- 步驟 2: 啟動模擬程序 ---
    print_test_step("啟動端到端模擬程序 (colab_run.py)")

    # 構造命令，確保使用 venv 中的 python
    # 我們將動態修改 sys.path 來找到模擬模組
    venv_python = ".venv/bin/python"
    mocks_path = str(Path.cwd() / "mocks")
    run_script = (
        f"import sys; "
        f"sys.path.insert(0, '{mocks_path}'); "
        f"import runpy; "
        f"runpy.run_path('colab_run.py', run_name='__main__')"
    )
    command = [venv_python, "-c", run_script]

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        preexec_fn=os.setsid if sys.platform != "win32" else None
    )
    print(f"INFO: 主模擬程序已啟動 (PID: {process.pid})。")

    # --- 步驟 3: 監控輸出並驗證 ---
    output_lines = []
    server_ready = False
    try:
        start_time = time.time()
        while time.time() - start_time < SIMULATION_TIMEOUT:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"[E2E_STDOUT] {line.strip()}")
                output_lines.append(line.strip())
                if "✅ 伺服器已在埠號" in line and "上線！" in line:
                    print("\n✅ 成功: 偵測到伺服器上線日誌！")
                    server_ready = True
                    break
        if not server_ready:
            raise RuntimeError(f"伺服器未能在 {SIMULATION_TIMEOUT} 秒內就緒。")

        # --- 步驟 4: 測試優雅關閉 ---
        print_test_step("測試優雅關閉")
        os.killpg(os.getpgid(process.pid), signal.SIGINT)
        process.wait(timeout=SHUTDOWN_WAIT_TIMEOUT)
        print("✅ 成功: 程序已關閉。")

        # --- 步驟 5: 驗證日誌歸檔 ---
        print_test_step("驗證日誌歸檔")
        archive_dir = Path(ARCHIVE_FOLDER_NAME)
        if not archive_dir.is_dir():
            raise FileNotFoundError("歸檔目錄未建立！")
        log_files = list(archive_dir.glob("鳳凰之心_作戰日誌_*.txt"))
        if not log_files:
            raise FileNotFoundError("日誌檔案未在歸檔目錄中找到！")
        if log_files[0].stat().st_size == 0:
            raise ValueError("日誌檔案為空！")
        print(f"✅ 成功: 找到非空的日誌檔案: {log_files[0]}")

    except Exception as e:
        print(f"\n❌❌❌ 端到端測試失敗: {e} ❌❌❌", file=sys.stderr)
        # 確保子進程被終止
        if process.poll() is None:
            print("INFO: 強制終止殘餘的模擬程序...", file=sys.stderr)
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        # 打印所有輸出以便調試
        print("\n--- [所有 STDOUT] ---", file=sys.stderr)
        print("\n".join(output_lines), file=sys.stderr)
        print("\n--- [所有 STDERR] ---", file=sys.stderr)
        print(process.stderr.read(), file=sys.stderr)
        sys.exit(1)

    print("\n🎉🎉🎉 所有端到端測試均已通過！ 🎉🎉🎉")
    sys.exit(0)


if __name__ == "__main__":
    main()
