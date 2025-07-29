# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 執行器 v1.0                                               ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       此腳本為在 Google Colab 環境中執行的前端介面。                 ║
# ║       它提供參數化設定，並將這些設定作為環境變數傳遞給後端的核心     ║
# ║       測試與啟動腳本。                                               ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心指揮中心 v1.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "2.1.2" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: E2E 測試參數**
#@markdown > **設定端對端測試的運行模式。**
#@markdown ---
#@markdown **測試模式 (TEST_MODE)**
#@markdown > **`mock` 模式運行速度快，不下載大型依賴；`real` 模式進行完整功能驗證。**
TEST_MODE = "real" #@param ["mock", "real"]

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心啟動器
# ==============================================================================
import os
import sys
import shutil
import subprocess
from pathlib import Path
import time

def colab_bootstrap():
    """
    一個穩健、簡潔的 Colab 啟動程序。
    """
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    try:
        from IPython.display import clear_output
        clear_output(wait=True)

        print("🚀 鳳凰之心 Colab 啟動程序...")
        print("="*80)

        # --- 步驟 1: 準備並下載專案 ---
        print(f"\n--- 步驟 1/4: 準備並下載專案 ---")
        if FORCE_REPO_REFRESH and project_path.exists():
            print(f"⚠️  偵測到「強制刷新」，正在刪除舊資料夾: {project_path}")
            shutil.rmtree(project_path)
            print("✅  舊資料夾已移除。")

        if not project_path.exists():
            print(f"🚀 開始從 GitHub (分支/標籤: {TARGET_BRANCH_OR_TAG}) 拉取程式碼...")
            git_command = ["git", "clone", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", REPOSITORY_URL, str(project_path)]
            subprocess.run(git_command, check=True, capture_output=True, text=True, encoding='utf-8', cwd=base_path)
            print("✅ 程式碼成功下載！")
        else:
            print(f"✅ 資料夾 '{project_path.name}' 已存在，跳過下載。")

        os.chdir(project_path)
        print(f"✅ 工作目錄已切換至: {os.getcwd()}")

        # --- 步驟 2: 安裝核心依賴 ---
        print(f"\n--- 步驟 2/4: 安裝核心依賴 ---")
        print("⏳ 正在安裝所有必要的依賴套件...")
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "pyyaml", "uv", "nest_asyncio", "httpx"], check=True)
        print("✅ 所有依賴套件已成功安裝。")

        # --- 步驟 3: 執行端對端測試 ---
        print(f"\n--- 步驟 3/4: 執行端對端測試 ---")
        print(f"🧪 正在以 '{TEST_MODE}' 模式啟動端對端測試...")

        test_env = os.environ.copy()
        test_env["TEST_MODE"] = TEST_MODE
        # 將 Colab 參數傳遞給測試腳本
        test_env["REPOSITORY_URL"] = REPOSITORY_URL
        test_env["TARGET_BRANCH_OR_TAG"] = TARGET_BRANCH_OR_TAG
        test_env["PROJECT_FOLDER_NAME"] = PROJECT_FOLDER_NAME

        result = subprocess.run(["python", "smart_e2e_test.py"], env=test_env, capture_output=True, text=True)

        print("--- STDOUT ---")
        print(result.stdout)
        print("--- STDERR ---")
        print(result.stderr)

        if result.returncode != 0:
            print("❌ 端對端測試失敗。無法繼續。請檢查上面的日誌輸出。")
            return # 測試失敗則中止

        print("✅ 端對端測試成功通過！")

        # --- 步驟 4: 啟動後端服務 ---
        print(f"\n--- 步驟 4/4: 啟動後端服務 ---")

        # 使用 nest_asyncio 來處理 Colab 的事件循環
        import nest_asyncio
        nest_asyncio.apply()

        from multiprocessing import Process
        from launch import main as launch_main

        def run_launcher():
            try:
                import asyncio
                asyncio.run(launch_main())
            except Exception as e:
                print(f"啟動服務時發生錯誤: {e}")

        print("🚀 正在背景啟動所有服務...")
        server_process = Process(target=run_launcher)
        server_process.start()
        print("✅ 所有服務應該已經在背景啟動。")

        # Colab 會自動將 localhost:8000 的連結轉換為可點擊的公開 URL
        proxy_url = "http://localhost:8000"

        print("\n" + "="*80)
        print("🎉 啟動程序已完成！ 🎉".center(80))
        print("\n")
        print(f"👉 請點擊以下連結，在新分頁中打開「即時監控儀表板」:")
        print(f"   {proxy_url}")
        print("\n")
        print("您可以在儀表板中觀察詳細的服務啟動進度。")
        print("請注意：關閉此 Colab 儲存格將會終止所有後端服務。")
        print("="*80)

        # 讓服務持續在背景運行，直到使用者手動停止儲存格
        server_process.join()

    except subprocess.CalledProcessError as e:
        print(f"\n💥 執行外部命令時發生錯誤！")
        print(f"   命令: {' '.join(e.cmd)}")
        stdout = e.stdout.strip() if hasattr(e, 'stdout') and e.stdout else ""
        stderr = e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else ""
        if stdout: print(f"   輸出:\n{stdout}")
        if stderr: print(f"   錯誤訊息:\n{stderr}")
    except Exception as e:
        import traceback
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        traceback.print_exc()

# --- 執行啟動程序 ---
colab_bootstrap()
