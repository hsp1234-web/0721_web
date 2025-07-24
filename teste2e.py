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
import re

# --- 常數設定 ---
SIMULATION_TIMEOUT = 60  # 秒，給予安裝依賴和啟動伺服器的完整時間
SHUTDOWN_WAIT_TIMEOUT = 15 # 秒，等待優雅關閉的時間
ARCHIVE_FOLDER_NAME = "combat_log_archive"

def print_test_step(message: str):
    """打印格式化的測試步驟標題。"""
    print(f"\n{'='*70}")
    print(f"🛰️  {message}")
    print(f"{'='*70}")

def cleanup_previous_run():
    """清理上一次測試可能留下的產物。"""
    print_test_step("清理環境")
    for folder in [ARCHIVE_FOLDER_NAME, ".venv", "mocks", "content"]:
        dir_path = Path(folder)
        if dir_path.exists():
            print(f"INFO: 正在刪除已存在的目錄: {dir_path}")
            shutil.rmtree(dir_path)
    print("✅ 清理完畢。")

def setup_colab_environment():
    """建立一個模擬的 Colab 環境結構。"""
    print_test_step("建立模擬 Colab 環境")
    content_web_dir = Path("content/WEB")
    content_web_dir.mkdir(parents=True, exist_ok=True)
    print(f"INFO: 已建立工作目錄: {content_web_dir}")

    # 複製應用程式檔案到模擬的 WEB 目錄
    source_files = [
        "apps", "static", "main.py", "run.py",
        "uv_manager.py", "requirements.txt",
        "colab_bootstrap.py", "colab_run.py"
    ]
    for item in source_files:
        src_path = Path(item)
        dst_path = content_web_dir / item
        if src_path.is_dir():
            shutil.copytree(src_path, dst_path)
        else:
            shutil.copy(src_path, dst_path)
    print(f"INFO: 已將應用程式檔案複製到 {content_web_dir}")
    print("✅ 模擬 Colab 環境已就緒。")

def main():
    """主測試函式。"""
    cleanup_previous_run()
    setup_colab_environment()

    # --- 步驟 1: 建立虛擬環境和模擬模組 ---
    # 這是為了解決 `colab_bootstrap.py` 的匯入問題所必需的準備工作
    print_test_step("準備測試環境 (venv & mocks)")
    try:
        # 在 content 目錄下建立 venv
        subprocess.run(["python3", "-m", "venv", "content/.venv"], check=True)

        # 建立模擬模組
        mocks_dir = Path("mocks")
        os.makedirs(f"{mocks_dir}/google/colab", exist_ok=True)
        os.makedirs(f"{mocks_dir}/IPython", exist_ok=True)
        Path(f"{mocks_dir}/__init__.py").touch()
        Path(f"{mocks_dir}/google/__init__.py").touch()
        Path(f"{mocks_dir}/google/colab/__init__.py").touch()
        Path(f"{mocks_dir}/IPython/__init__.py").touch()
        # 模擬 google.colab.output 的核心函式
        with open(f"{mocks_dir}/google/colab/output.py", "w") as f:
            f.write('def get_colab_url(port, timeout_sec=20, **kwargs): return f"http://mock-colab-url-for-port-{port}"\n')
            f.write('def display(*args, **kwargs): print(f"MockDisplay: {args}")\n')
            f.write('def update_display(*args, **kwargs): print(f"MockUpdateDisplay: {args}")\n')
            f.write('def HTML(s): return f"HTML_CONTENT: {s}"\n')
        # 模擬 IPython.display
        with open(f"{mocks_dir}/IPython/display.py", "w") as f:
            f.write('def display(*args, **kwargs): print(f"MockDisplay: {args}")\n')
            f.write('def update_display(*args, **kwargs): print(f"MockUpdateDisplay: {args}")\n')
            f.write('def HTML(s): return f"HTML_CONTENT: {s}"\n')
        print("✅ 虛擬環境和模擬模組已建立。")

        # 安裝 bootstrap 自身需要的依賴
        print("INFO: 正在為 bootstrap 安裝 'psutil' 和 'IPython'...")
        venv_pip = "content/.venv/bin/pip"
        subprocess.run([venv_pip, "install", "psutil", "ipython"], check=True, capture_output=True)
        print("✅ 'psutil' 和 'IPython' 已安裝。")

    except Exception as e:
        print(f"❌ 致命錯誤: 準備環境時失敗: {e}", file=sys.stderr)
        sys.exit(1)

    # --- 步驟 2: 啟動模擬程序 ---
    print_test_step("啟動端到端模擬程序 (colab_run.py)")

    # 構造命令，確保在正確的 CWD 下使用 venv 中的 python
    # 我們將動態修改 sys.path 來找到 mocks 目錄 (它在專案根目錄)
    venv_python = "../.venv/bin/python" # 從 content/WEB 指向 .venv
    cwd = Path.cwd()
    mocks_path = str(cwd / "mocks")
    bootstrap_script_path = str(cwd / "content/WEB/colab_run.py")

    # 構造參數直接呼叫 colab_bootstrap.py
    bootstrap_script_path = "colab_bootstrap.py"
    command = [
        venv_python,
        bootstrap_script_path,
        "--log-lines", "50",
        "--refresh-interval", "0.2",
        "--target-folder", ".", # 在 WEB 目錄下，所以 target 是 '.'
        "--archive-folder", str(cwd / ARCHIVE_FOLDER_NAME), # 使用絕對路徑
        "--port", "8000",
    ]

    # 我們需要設定 PYTHONPATH 來讓 bootstrap 找到模擬模組
    env = os.environ.copy()
    env["PYTHONPATH"] = mocks_path + os.pathsep + env.get("PYTHONPATH", "")

    process = subprocess.Popen(
        command,
        cwd="content/WEB", # 在 'content/WEB' 目錄下執行
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        env=env, # 傳遞修改後的環境變數
        preexec_fn=os.setsid if sys.platform != "win32" else None
    )
    print(f"INFO: 主模擬程序已啟動 (PID: {process.pid})。")

    # --- 步驟 3: 監控輸出並驗證 ---
    output_lines = []
    server_ready = False
    try:
        start_time = time.time()
        # --- 新增：更嚴格的日誌驗證 ---
        expected_patterns = {
            "dependency_install": re.compile(r"INFO: --- \[uv_manager\] 所有依賴項均已成功安裝！ ---"),
            "server_starting": re.compile(r"INFO: 準備啟動後端伺服器 \(run.py\)..."),
            "uvicorn_info": re.compile(r"INFO:     Uvicorn running on http://127.0.0.1:8000"),
            "server_ready": re.compile(r"SUCCESS: ✅ 伺服器已在埠號 8000 上線！")
        }
        found_patterns = set()

        while time.time() - start_time < SIMULATION_TIMEOUT:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"[E2E_STDOUT] {line.strip()}")
                output_lines.append(line.strip())
                for name, pattern in expected_patterns.items():
                    if name not in found_patterns and pattern.search(line):
                        print(f"✅ 驗證點通過: {name}")
                        found_patterns.add(name)

                if "server_ready" in found_patterns:
                    server_ready = True
                    break

        # 驗證所有模式都已找到
        missing_patterns = set(expected_patterns.keys()) - found_patterns
        if missing_patterns:
            raise RuntimeError(f"測試失敗，缺少關鍵日誌輸出: {missing_patterns}")

        if not server_ready:
            raise RuntimeError(f"伺服器未能在 {SIMULATION_TIMEOUT} 秒內就緒。")

        # --- 步驟 4: 測試優雅關閉 ---
        print_test_step("測試優雅關閉")
        os.killpg(os.getpgid(process.pid), signal.SIGINT)
        process.wait(timeout=SHUTDOWN_WAIT_TIMEOUT)
        print("✅ 成功: 程序已關閉。")

        # --- 步驟 5: 驗證日誌歸檔 ---
        print_test_step("驗證日誌歸檔")
        # 注意：歸檔目錄現在是在專案根目錄，而不是在 content/WEB 裡
        archive_dir = Path.cwd() / ARCHIVE_FOLDER_NAME
        if not archive_dir.is_dir():
            raise FileNotFoundError(f"歸檔目錄未建立於: {archive_dir}")
        log_files = list(archive_dir.glob("phoenix_heart_combat_log_*.txt"))
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
