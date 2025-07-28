# -*- coding: utf-8 -*-
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║                                                                                 ║
# ║      🚀 鳳凰之心 Colab 獨立啟動腳本 v2.0 (Jules 設計)                           ║
# ║                                                                                 ║
# ║   這是一個獨立的 Python 腳本，專為在 Google Colab 環境中執行而設計。            ║
# ║   它將所有設定參數集中在頂部，您可以直接複製全部程式碼到一個 Colab 儲存格中，   ║
# ║   修改參數後直接執行，即可完成所有啟動步驟。                                   ║
# ║                                                                                 ║
# ╚═════════════════════════════════════════════════════════════════════════════╝

# ====================================================================================
# Part 1: 參數設定區 (請在此處完成所有設定)
# ====================================================================================

# --- 1. 核心設定 ---
# 啟動模式: "DASHBOARD" 或 "API_ONLY"
# - "DASHBOARD": 啟動一個基於網頁的互動式終端，您可以在其中監控服務狀態。(推薦)
# - "API_ONLY": 在背景啟動 `quant` 和 `transcriber` 兩個 API 服務，並提供公開網址。
啟動模式 = "DASHBOARD"

# --- 2. 原始碼設定 ---
程式碼倉庫網址 = "https://github.com/hsp1234-web/0721_web"
要使用的版本分支或標籤 = "3.1.0"
專案資料夾名稱 = "WEB"
# 是否強制刷新程式碼: 如果為 True，將會刪除舊的程式碼，從 GitHub 重新下載最新版本。
是否強制刷新程式碼 = True

# --- 3. 安裝與服務設定 ---
# 安裝模式: "FULL" 或 "CORE"
# - "FULL": 完整安裝，包含大型依賴 (如 PyTorch)。
# - "CORE": 模擬安裝，僅安裝核心依賴，啟動速度快。
安裝模式 = "FULL" # 對應您範本的 "完整安裝 (包含大型依賴)"

量化分析服務埠號 = 8001
語音轉寫服務埠號 = 8002

# --- 4. 測試與日誌設定 ---
# 是否執行啟動後測試: 服務啟動後，會自動透過公開網址測試 API 連線。
是否執行啟動後測試 = True
日誌歸檔資料夾 = "作戰日誌"
時區 = "Asia/Taipei"

# --- 5. (可選) FinMind API Token ---
# 如果您需要 `quant` 服務實際運作，請填寫您的 FinMind API Token。
FINMIND_API_TOKEN = ""


# ====================================================================================
# Part 2: 核心執行邏輯 (通常無需修改)
# ====================================================================================
import os
import sys
import shutil
import subprocess
import shlex
from pathlib import Path

def setup_colab_environment():
    """安裝 Colab 環境需要的套件並回傳是否在 Colab 中執行"""
    try:
        # 安裝 `get_ipython` 需要的套件
        subprocess.check_call([sys.executable, "-m", "pip", "-q", "install", "ipython"])
        return True
    except ImportError:
        return False

IS_COLAB = setup_colab_environment()

def print_header(message):
    print(f"\n{'='*60}\n🚀 {message}\n{'='*60}")

def run_command(command, cwd):
    """執行命令並顯示輸出"""
    print(f"ℹ️ 在 '{cwd}' 中執行: {command}")
    try:
        subprocess.run(
            shlex.split(command),
            check=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令 '{command}' 執行失敗，返回碼: {e.returncode}")
        return False
    return True

# --- 主要執行流程 ---
def main():
    print_header("鳳凰之心 Colab 啟動程序開始")

    # 步驟 1: 準備專案資料夾
    base_path = Path("/content") if IS_COLAB else Path.cwd()
    project_path = base_path / 專案資料夾名稱

    if 是否強制刷新程式碼 and project_path.exists():
        print(f"🧹 偵測到強制刷新，正在移除舊資料夾: {project_path}")
        shutil.rmtree(project_path)

    if not project_path.exists():
        print("📂 正在從 GitHub 下載專案程式碼...")
        clone_command = f"git clone --branch {要使用的版本分支或標籤} --depth 1 {程式碼倉庫網址} {project_path}"
        if not run_command(clone_command, base_path):
            print("❌ 程式碼下載失敗，啟動中止。")
            return
    else:
        print("✅ 專案資料夾已存在，跳過下載。")

    os.chdir(project_path)
    print(f"✅ 已將工作目錄切換至: {os.getcwd()}")

    # 步驟 2: 執行核心啟動腳本
    # 我們將直接呼叫專案內的 `launch.py` 來處理環境設定和啟動
    launch_script_path = project_path / "scripts" / "launch.py"

    if not launch_script_path.exists():
        print(f"❌ 錯誤: 找不到核心啟動腳本: {launch_script_path}")
        print("請確認您的專案結構是否正確。")
        return

    # 步驟 3: 根據啟動模式執行
    if 啟動模式.upper() == "DASHBOARD":
        print_header("啟動模式: 視覺化儀表板")
        if IS_COLAB:
            from google.colab.output import eval_js
            dashboard_url = eval_js('google.colab.kernel.proxyPort(8080)')
            print(f"\n🌍 您的儀表板網址 (請在新分頁中開啟): {dashboard_url}\n")

        print("儀表板將會佔用此儲存格的輸出，您可以直接與其互動。")
        print("-" * 60)

        # 使用 IPython 的 system call 來執行，以便在 Colab 中正確顯示輸出
        if IS_COLAB:
            from IPython import get_ipython
            get_ipython().system(f"python {launch_script_path} --dashboard")
        else:
            run_command(f"python {launch_script_path} --dashboard", project_path)

    elif 啟動模式.upper() == "API_ONLY":
        print_header("啟動模式: 僅 API 服務")

        # 設定環境變數
        os.environ['FINMIND_API_TOKEN'] = FINMIND_API_TOKEN
        # 將埠號設定傳遞給 launch.py (假設 launch.py 可以讀取環境變數)
        os.environ['QUANT_PORT'] = str(量化分析服務埠號)
        os.environ['TRANSCRIBER_PORT'] = str(語音轉寫服務埠號)
        os.environ['TIMEZONE'] = 時區

        if IS_COLAB:
            from google.colab.output import eval_js
            quant_url = eval_js(f'google.colab.kernel.proxyPort({量化分析服務埠號})')
            transcriber_url = eval_js(f'google.colab.kernel.proxyPort({語音轉寫服務埠號})')
            print("\n🌍 您的服務 API 網址:")
            print(f"  - 量化分析服務: {quant_url}")
            print(f"  - 語音轉寫服務: {transcriber_url}")

        print("\n正在背景啟動服務，請稍候...")

        # 使用 nohup 和 & 在背景啟動服務
        log_file = "api_services.log"
        command = f"nohup python {launch_script_path} > {log_file} 2>&1 &"

        if IS_COLAB:
            from IPython import get_ipython
            get_ipython().system(command)
        else:
            # 在本地環境，我們需要用不同的方式處理背景程序
            subprocess.Popen(shlex.split(f"python {launch_script_path}"), stdout=open(log_file, 'w'), stderr=subprocess.STDOUT)

        print(f"\n✅ API 服務已在背景啟動。")
        print(f"日誌檔案已儲存至 '{log_file}'。")

        if 是否執行啟動後測試:
            # 這裡可以加入呼叫 API 進行測試的程式碼
            print("\n💡 提示: 啟動後測試功能尚未在此版本中完全實現。")
            print("您可以手動訪問上面的 /docs 路徑來驗證服務。")

    else:
        print(f"❌ 無效的啟動模式: '{啟動模式}'。請選擇 'DASHBOARD' 或 'API_ONLY'。")

if __name__ == "__main__":
    # 為了能在 Colab 儲存格中直接執行，我們把 main() 包裝起來
    try:
        main()
    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print("❌ 在執行過程中發生了無法預期的錯誤:")
        traceback.print_exc()
        print("="*60)
