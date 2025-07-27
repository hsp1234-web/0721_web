#@title 💎 鳳凰之心指揮中心 v10.1 (數字輸入版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤，以及專案資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "2.1.0" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 應用程式參數**
#@markdown > **設定指揮中心的核心運行參數。**
#@markdown ---
#@markdown #### **⏱️ 儀表板更新頻率 (秒)**
#@markdown > **控制儀表板畫面每秒刷新的次數。較小的值 (如 0.1) 會讓動畫更流暢，但會消耗更多 CPU 資源；較大的值 (如 1.0) 會降低 CPU 消耗，但畫面更新會有停頓感。建議值為 0.25。**
REFRESH_RATE_SECONDS = 0.2 #@param {type:"number"}
#@markdown ---
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
LOG_DISPLAY_LINES = 20 #@param {type:"integer"}
#@markdown **日誌歸檔資料夾 (LOG_ARCHIVE_FOLDER_NAME)**
#@markdown > **留空即關閉歸檔功能。**
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔" #@param {type:"string"}
#@markdown **時區設定 (TIMEZONE)**
TIMEZONE = "Asia/Taipei" #@param {type:"string"}

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心啟動器 v10.1
# ==============================================================================
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path
from IPython.display import clear_output

def bootstrap():
    """準備環境並啟動鳳凰之心指揮中心。"""
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    try:
        clear_output(wait=True)
        print("🚀 鳳凰之心 v10.1 [數字輸入版] 啟動程序...")
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
            subprocess.run(git_command, check=True, capture_output=True, text=True, encoding='utf-8', cwd=base_path)
            print("✅ 程式碼成功下載！")
        else:
            print(f"✅ 資料夾 '{project_path.name}' 已存在，跳過下載。")

        # --- 步驟 3: 設定 Python 環境 ---
        print("\n--- 步驟 3/4: 設定 Python 環境 ---")
        os.chdir(project_path)
        if str(project_path) not in sys.path:
            sys.path.insert(0, str(project_path))

        # 將 scripts 目錄也加入路徑
        scripts_path = project_path / "scripts"
        if str(scripts_path) not in sys.path:
            sys.path.insert(0, str(scripts_path))

        print(f"✅ 已切換至專案目錄: {os.getcwd()}")

        print("\n--- 步驟 4/4: 安裝與啟動 ---")
        requirements_path = project_path / "requirements" / "colab.txt"
        if requirements_path.exists():
            subprocess.run(f"pip install -q -r {requirements_path}", shell=True, check=True)
            print("✅ 套件安裝完成。")

        print("\n🚀 正在匯入並啟動指揮中心...")
        module_name_to_clear = "colab_run"
        if module_name_to_clear in sys.modules:
            del sys.modules[module_name_to_clear]
            print(f"✅ 已清除 '{module_name_to_clear}' 的記憶體快取，確保載入最新版本。")

        print("所有後續輸出將由 DisplayManager 全權接管...")
        time.sleep(2)

        from colab_run import run_phoenix_heart

        run_phoenix_heart(
            log_lines=LOG_DISPLAY_LINES,
            archive_folder_name=LOG_ARCHIVE_FOLDER_NAME,
            timezone=TIMEZONE,
            project_path=project_path,
            base_path=base_path,
            refresh_rate=REFRESH_RATE_SECONDS # 將新參數傳遞給後端
        )

    except subprocess.CalledProcessError as e:
        print(f"\n💥 Git 下載失敗！\nGit 錯誤訊息: {e.stderr.strip()}")
    except Exception as e:
        import traceback
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        traceback.print_exc()

# --- 執行啟動程序 ---
bootstrap()
