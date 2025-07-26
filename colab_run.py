
#1
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
    def __init__(self, config=None):
        self.project_name = "鳳凰之心"
        self.version = "v17.2" # 更新版本號
        self.venv_dir = Path(".venv")
        self.is_in_colab = 'COLAB_GPU' in os.environ
        # 保存從儀表板傳入的設定，雖然目前沒用到但保留彈性
        self.config = config if config else {}

    def _run_command(self, command, shell=False, check=True):
        """執行一個 shell 指令並顯示其輸出。"""
        print(f"🚀  執行指令: {' '.join(command) if isinstance(command, list) else command}")
        try:
            # 在 Colab 中，我們需要確保使用 UTF-8 編碼
            encoding = 'utf-8' if self.is_in_colab else None
            subprocess.run(command, shell=shell, check=check, encoding=encoding, text=True)
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
        # 注意：這裡我們直接執行 server_main.py，它應該會使用傳入的 config
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
        python_executable = self.venv_dir / "bin" / "python" if sys.platform != "win32" else self.venv_dir / "Scripts" / "python.exe"

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

def main(config=None):
    """
    專案主執行入口點。
    這個函式會被 Colab 儀表板或其他外部腳本呼叫。
    """
    cockpit = Cockpit(config)
    cockpit.start_sequence()

if __name__ == "__main__":
    # 這個區塊讓此腳本也能夠被直接執行 (python colab_run.py)
    # 為了能獨立執行，提供一個空的 config
    print("以獨立腳本模式執行...")
    main(config={})
