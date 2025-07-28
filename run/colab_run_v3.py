# -*- coding: utf-8 -*-
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║                                                                                 ║
# ║      🚀 鳳凰之心 Colab 獨立啟動腳本 v3.0 (Jules 設計)                           ║
# ║      (健壯、可控、可驗證)                                                       ║
# ║                                                                                 ║
# ╚═════════════════════════════════════════════════════════════════════════════╝

# ====================================================================================
# Part 1: 參數設定區 (請在此處完成所有設定)
# ====================================================================================

# --- 1. 原始碼設定 ---
GIT_REPO_URL = "https://github.com/hsp1234-web/0721_web"
GIT_BRANCH = "main" # 您可以指定任何分支或標籤
PROJECT_DIR_NAME = "PHOENIX_HEART"
FORCE_REFRESH_CODE = True

# --- 2. 服務設定 ---
QUANT_PORT = 9001  # 使用一個非預設的埠號來測試參數傳遞
TRANSCRIBER_PORT = 9002
TIMEZONE = "America/New_York" # 使用一個非預設的時區來測試

# --- 3. 測試設定 ---
RUN_POST_LAUNCH_TESTS = True

# ====================================================================================
# Part 2: 核心啟動管理器 (通常無需修改)
# ====================================================================================
import os
import sys
import shutil
import subprocess
import shlex
import signal
import time
import atexit
from pathlib import Path

class ColabManager:
    """一個用於管理 Colab 中背景服務的類別"""

    def __init__(self, project_dir_name):
        self.project_path = Path(f"/content/{project_dir_name}")
        self.main_process = None
        self.is_colab = 'google.colab' in sys.modules
        atexit.register(self.cleanup)

    def print_header(self, message):
        print(f"\n{'='*60}\n🚀 {message}\n{'='*60}")

    def _run_command(self, command, cwd, bg=False):
        print(f"ℹ️ 在 '{cwd}' 中執行: {command}")
        if bg:
            return subprocess.Popen(
                shlex.split(command),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace'
            )
        try:
            subprocess.run(shlex.split(command), check=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 命令執行失敗，返回碼: {e.returncode}")
            return False

    def prepare_project(self, repo_url, branch, force_refresh):
        self.print_header("步驟 1/5: 準備專案程式碼")
        if force_refresh and self.project_path.exists():
            print(f"🧹 偵測到強制刷新，正在移除舊資料夾...")
            shutil.rmtree(self.project_path)

        if not self.project_path.exists():
            print("📂 正在從 GitHub 下載專案...")
            clone_cmd = f"git clone --branch {branch} --depth 1 {repo_url} {self.project_path}"
            if not self._run_command(clone_cmd, Path("/content")): return False

        os.chdir(self.project_path)
        print(f"✅ 已將工作目錄切換至: {os.getcwd()}")
        return True

    def prepare_environment(self):
        self.print_header("步驟 2/5: 準備 Python 環境")
        # 利用 launch.py 的 --prepare-only 功能來安裝所有依賴
        prepare_cmd = f"python scripts/launch.py --prepare-only"
        if not self._run_command(prepare_cmd, self.project_path): return False
        print("✅ Python 環境和依賴已準備就緒。")
        return True

    def launch_services(self, quant_port, transcriber_port, timezone):
        self.print_header("步驟 3/5: 在背景啟動服務")
        launch_cmd = (
            f"python scripts/launch.py "
            f"--port-quant {quant_port} "
            f"--port-transcriber {transcriber_port} "
            f"--timezone '{timezone}'"
        )
        self.main_process = self._run_command(launch_cmd, self.project_path, bg=True)

        if self.main_process:
            print(f"✅ 主啟動程序已在背景啟動 (PID: {self.main_process.pid})。")
            print("正在等待服務上線...")
            time.sleep(15) # 等待服務完成啟動
            return True
        else:
            print("❌ 啟動服務失敗。")
            return False

    def verify_services(self, quant_port, timezone):
        self.print_header("步驟 4/5: 驗證服務組態")
        if not RUN_POST_LAUNCH_TESTS:
            print("⚪ 已跳過啟動後測試。")
            return True

        try:
            import httpx
        except ImportError:
            self._run_command("pip install -q httpx", self.project_path)
            import httpx

        health_url = f"http://localhost:{quant_port}/health"
        try:
            print(f"正在向 {health_url} 發送請求...")
            response = httpx.get(health_url, timeout=10)
            response.raise_for_status()
            data = response.json()

            print(f"收到的組態: {data.get('config')}")

            # 驗證埠號和時區
            assert str(data['config']['port']) == str(quant_port)
            assert data['config']['timezone'] == timezone

            print("✅ 服務驗證成功！參數已正確傳遞並應用。")
            return True
        except Exception as e:
            print(f"❌ 服務驗證失敗: {e}")
            print("--- 主啟動程序日誌 ---")
            for line in self.main_process.stdout:
                print(line.strip())
            return False

    def cleanup(self):
        self.print_header("程序結束，執行清理工作")
        if self.main_process and self.main_process.poll() is None:
            print(f"正在向主程序 (PID: {self.main_process.pid}) 發送 SIGTERM 訊號...")
            self.main_process.terminate()
            try:
                self.main_process.wait(timeout=10)
                print("✅ 主程序已成功終止。")
            except subprocess.TimeoutExpired:
                print("⚠️ 主程序未能及時終止，強制結束。")
                self.main_process.kill()
        else:
            print("⚪ 無需清理，主程序未在運行或已結束。")

    def run(self):
        """執行完整流程"""
        try:
            if not self.prepare_project(GIT_REPO_URL, GIT_BRANCH, FORCE_REFRESH_CODE): return
            if not self.prepare_environment(): return
            if not self.launch_services(QUANT_PORT, TRANSCRIBER_PORT, TIMEZONE): return
            if not self.verify_services(QUANT_PORT, TIMEZONE): return

            self.print_header("步驟 5/5: 服務運行中")
            print("所有服務已在背景成功啟動並驗證。")
            print("這個 Colab 儲存格將保持活躍以維持服務運行。")
            print("您可以隨時手動中斷 (Interrupt) 執行來關閉所有服務。")

            # 保持腳本運行，同時監控主程序日誌
            while self.main_process.poll() is None:
                 for line in self.main_process.stdout:
                    print(f"[LAUNCHER]: {line.strip()}")
                 time.sleep(1)

        except KeyboardInterrupt:
            print("\n🛑 收到手動中斷信號。")
        finally:
            self.cleanup()

# ====================================================================================
# Part 3: 執行入口
# ====================================================================================
if __name__ == "__main__":
    manager = ColabManager(PROJECT_DIR_NAME)
    manager.run()
