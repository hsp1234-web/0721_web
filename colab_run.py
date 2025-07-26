import os
import subprocess
import sys
from pathlib import Path

class Cockpit:
    """
    鳳凰之心專案的啟動駕駛艙。
    這個類別會自動偵測執行環境 (Google Colab 或標準環境)，
    並採取最適合的啟動流程。
    """
    def __init__(self):
        self.project_name = "鳳凰之心"
        self.version = "v17.1"
        self.venv_dir = Path(".venv")
        self.is_in_colab = 'COLAB_GPU' in os.environ

    def _run_command(self, command, shell=False, check=True):
        """執行一個 shell 指令並顯示其輸出。"""
        print(f"🚀  執行指令: {' '.join(command) if isinstance(command, list) else command}")
        try:
            # 在 Colab 中，我們需要確保使用 UTF-8 編碼
            encoding = 'utf-8' if self.is_in_colab else None
            subprocess.run(command, shell=shell, check=check, encoding=encoding)
            print("✅  指令成功執行。")
        except subprocess.CalledProcessError as e:
            print(f"❌  指令執行失敗: {e}")
            sys.exit(1) # 發生錯誤時終止程式

    def start_sequence(self):
        """啟動主序列。"""
        print(f">>> {self.project_name} {self.version} 駕駛艙啟動序列 <<<")
        
        if self.is_in_colab:
            self.run_in_colab()
        else:
            self.run_in_standard_env()

    def run_in_colab(self):
        """
        在 Google Colab 環境中的執行流程。
        這個流程會跳過建立虛擬環境的步驟，直接安裝套件。
        """
        print("\n🛰️  偵測到 Google Colab 環境，啟用 Colab 專用啟動模式...")
        
        # 步驟 1: 安裝所有必要的套件
        print("\n--- 步驟 1/2: 安裝 Colab 環境所需套件 ---")
        requirements_path = "requirements/colab.txt"
        if not Path(requirements_path).exists():
            print(f"❌ 錯誤: 找不到 {requirements_path} 檔案。")
            sys.exit(1)
        
        # 直接使用 pip 安裝
        self._run_command([sys.executable, "-m", "pip", "install", "-r", requirements_path])
        
        # 步驟 2: 啟動主伺服器程式
        print("\n--- 步驟 2/2: 啟動應用程式主伺服器 ---")
        self._run_command([sys.executable, "server_main.py"])
        
        print(f"\n🎉 {self.project_name} 已在 Colab 環境中成功啟動！")

    def run_in_standard_env(self):
        """
        在標準環境 (例如: 本機、Ubuntu 伺服器) 中的執行流程。
        這個流程會建立並使用虛擬環境。
        """
        print("\n💻  偵測到標準執行環境，啟用虛擬環境啟動模式...")

        # 步驟 1: 建立虛擬環境
        print("\n--- 步驟 1/4: 檢查並建立 Python 虛擬環境 ---")
        if not self.venv_dir.exists():
            print(f"偵測到尚未建立虛擬環境，現在開始建立於: {self.venv_dir}")
            self._run_command([sys.executable, "-m", "venv", str(self.venv_dir)])
        else:
            print("偵測到現有虛擬環境，跳過建立步驟。")
        
        # 根據作業系統決定 Python 解譯器路徑
        if sys.platform == "win32":
            python_executable = self.venv_dir / "Scripts" / "python.exe"
        else:
            python_executable = self.venv_dir / "bin" / "python"

        # 步驟 2: 安裝 uv 加速器
        print("\n--- 步驟 2/4: 在虛擬環境中安裝 uv 加速器 ---")
        self._run_command([str(python_executable), "-m", "pip", "install", "uv"])

        # 步驟 3: 安裝專案依賴套件
        print("\n--- 步驟 3/4: 使用 uv 安裝專案依賴套件 ---")
        requirements_path = "requirements/base.txt"
        self._run_command([str(python_executable), "-m", "uv", "pip", "install", "-r", requirements_path])

        # 步驟 4: 啟動主伺服器程式
        print("\n--- 步驟 4/4: 在虛擬環境中啟動應用程式主伺服器 ---")
        self._run_command([str(python_executable), "server_main.py"])

        print(f"\n🎉 {self.project_name} 已在標準環境中成功啟動！")


if __name__ == "__main__":
    cockpit = Cockpit()
    cockpit.start_sequence()
