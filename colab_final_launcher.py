#@title 💎 鳳凰之心指揮中心 v11 (最終穩定版) { vertical-output: true, display-mode: "form" }
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
#@markdown ### **Part 2: 應用程式參數**
#@markdown > **這些參數將會傳遞給您的應用程式。**
#@markdown ---
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
LOG_DISPLAY_LINES = 20 #@param {type:"integer"}
#@markdown **日誌歸檔資料夾 (LOG_ARCHIVE_FOLDER_NAME)**
#@markdown > **留空即關閉歸檔功能。**
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **時區設定 (TIMEZONE)**
TIMEZONE = "Asia/Taipei" #@param {type:"string"}
#@markdown **儀表板更新頻率 (秒) (REFRESH_RATE_SECONDS)**
REFRESH_RATE_SECONDS = 0.25 #@param {type:"number"}

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心啟動器 v11 (K.I.S.S. 原則版)
# ==============================================================================
import os
import sys
import shutil
import subprocess
from pathlib import Path

def simple_bootstrap():
    """
    一個更簡單、更穩健的啟動程序，嚴格遵循 Colab 的執行邏輯。
    Keep It Simple, Stupid!
    """
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    try:
        print("🚀 鳳凰之心 v11 [最終穩定版] 啟動程序...")
        print("="*80)

        # --- 步驟 1: 準備下載目錄 ---
        print("\n--- 步驟 1/4: 準備下載目錄 ---")
        if FORCE_REPO_REFRESH and project_path.exists():
            print(f"⚠️  偵測到「強制刷新」，正在刪除舊資料夾: {project_path}")
            shutil.rmtree(project_path)
            print("✅  舊資料夾已移除。")

        # --- 步驟 2: 下載程式碼 ---
        print("\n--- 步驟 2/4: 下載程式碼 ---")
        if not project_path.exists():
            print(f"🚀 開始從 GitHub (分支/標籤: {TARGET_BRANCH_OR_TAG}) 拉取程式碼...")
            git_command = ["git", "clone", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", REPOSITORY_URL, str(project_path)]
            subprocess.run(git_command, check=True, capture_output=True, text=True, encoding='utf-8')
            print("✅ 程式碼成功下載！")
        else:
            print(f"✅ 資料夾 '{project_path.name}' 已存在，跳過下載。")

        # --- 步驟 3: 切換工作目錄並安裝依賴 ---
        print("\n--- 步驟 3/4: 設定環境並安裝依賴 ---")
        os.chdir(project_path)
        print(f"✅ 工作目錄已成功切換至: {os.getcwd()}")

        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            print(f"✅ 找到依賴套件檔案: {requirements_path}")
            # 安裝 uv 來加速
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "uv"], check=True)
            # 使用 uv 安裝
            subprocess.run(["uv", "pip", "install", "-q", "-r", str(requirements_path)], check=True)
            print("✅ 所有依賴套件已成功安裝。")
        else:
            print(f"⚠️  警告：找不到 '{requirements_path}'，跳過依賴安裝。")

        # --- 步驟 4: 執行主應用程式 ---
        print("\n--- 步驟 4/4: 執行主應用程式 ---")
        print("🚀 即將把控制權完全交給 'scripts/colab_run.py'...")
        print("="*80)

        # 設定環境變數，將 Colab 參數傳遞給子程序
        env = os.environ.copy()
        env["LOG_DISPLAY_LINES"] = str(LOG_DISPLAY_LINES)
        env["LOG_ARCHIVE_FOLDER_NAME"] = str(LOG_ARCHIVE_FOLDER_NAME)
        env["TIMEZONE"] = str(TIMEZONE)
        env["REFRESH_RATE_SECONDS"] = str(REFRESH_RATE_SECONDS)
        env["PROJECT_PATH"] = str(project_path)
        env["BASE_PATH"] = str(base_path)

        # 直接執行 scripts/colab_run.py
        # 這可以確保它在正確的工作目錄和已安裝好依賴的環境中運行
        subprocess.run([sys.executable, "scripts/colab_run.py"], env=env, check=True)

    except subprocess.CalledProcessError as e:
        print(f"\n💥 執行外部命令時發生錯誤！")
        print(f"   命令: {' '.join(e.cmd)}")
        if e.stdout:
            print(f"   輸出:\n{e.stdout}")
        if e.stderr:
            print(f"   錯誤訊息:\n{e.stderr}")
    except Exception as e:
        import traceback
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        traceback.print_exc()

# --- 執行啟動程序 ---
simple_bootstrap()
