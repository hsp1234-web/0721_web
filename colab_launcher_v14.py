# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 儲存格 v14 (最終穩定版)                                   ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       本版本遵循 v10.1 的簡潔設計，將啟動器與核心邏輯分離。         ║
# ║       啟動器 (Launcher) 專注於環境準備，核心邏輯 (Core) 則由        ║
# ║       一個獨立的腳本 `scripts/colab_run.py` 處理。                   ║
# ║                                                                      ║
# ║   v14 更新 (Jules 修正):                                             ║
# ║       - 新增進度條：移除 `pip install` 的 `-q` 參數，在安裝時顯示進度。 ║
# ║       - 解決埠衝突：由 `scripts/colab_run.py` 內部自動清理已佔用的埠。 ║
# ║       - 根除匯入錯誤：採用 `subprocess` 執行核心邏輯，而非 `import`。  ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心指揮中心 v14 (最終穩定版) { vertical-output: true, display-mode: "form" }
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
#@markdown > **設定指揮中心的核心運行參數。**
#@markdown ---
#@markdown **儀表板更新頻率 (秒) (REFRESH_RATE_SECONDS)**
REFRESH_RATE_SECONDS = 0.25 #@param {type:"number"}
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
# 🚀 核心啟動器 v13
# ==============================================================================
import os
import sys
import shutil
import subprocess
from pathlib import Path

def phoenix_bootstrap():
    """
    一個穩健、簡潔的啟動程序，遵循 v10.1 的分離式設計哲學。
    """
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

    try:
        # 在 Colab 中，clear_output 是可用的
        from IPython.display import clear_output
        clear_output(wait=True)

        print("🚀 鳳凰之心 v13 [鳳凰版] 啟動程序...")
        print("="*80)

        # --- 步驟 1: 準備下載目錄 ---
        print(f"\n--- 步驟 1/4: 準備下載目錄 ---")
        if FORCE_REPO_REFRESH and project_path.exists():
            print(f"⚠️  偵測到「強制刷新」，正在刪除舊資料夾: {project_path}")
            shutil.rmtree(project_path)
            print("✅  舊資料夾已移除。")

        # --- 步驟 2: 下載程式碼 ---
        print(f"\n--- 步驟 2/4: 下載程式碼 ---")
        # 關鍵修正：在執行任何檔案操作前，確保 base_path 存在
        base_path.mkdir(exist_ok=True)

        if not project_path.exists():
            print(f"🚀 開始從 GitHub (分支/標籤: {TARGET_BRANCH_OR_TAG}) 拉取程式碼...")
            # 使用 -q (quiet) 選項來減少不必要的 git 輸出
            git_command = ["git", "clone", "-q", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", REPOSITORY_URL, str(project_path)]
            # 關鍵修正：明確指定 git 的工作目錄為 base_path，以避免 "Unable to read CWD" 的錯誤
            subprocess.run(git_command, check=True, capture_output=True, text=True, encoding='utf-8', cwd=base_path)
            print("✅ 程式碼成功下載！")
        else:
            print(f"✅ 資料夾 '{project_path.name}' 已存在，跳過下載。")

        # --- 步驟 3: 切換目錄並安裝依賴 ---
        print(f"\n--- 步驟 3/4: 設定環境並安裝依賴 ---")
        os.chdir(project_path)
        print(f"✅ 工作目錄已切換至: {os.getcwd()}")

        requirements_path = Path("requirements.txt")
        if requirements_path.exists():
            print("⏳ 正在安裝所有必要的依賴套件，將顯示進度條...")
            # 首先確保核心套件存在 (移除 -q 以顯示進度)
            subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "pytz", "IPython"], check=True)
            # 然後安裝專案指定的其他套件 (移除 -q 以顯示進度)
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(requirements_path)], check=True)
            print("✅ 所有依賴套件已成功安裝。")
        else:
            print(f"⚠️  警告：找不到 'requirements.txt'，跳過依賴安裝。")

        # --- 步驟 4: 執行核心邏輯 ---
        print(f"\n--- 步驟 4/4: 執行核心邏輯 ---")
        print("🚀 即將把控制權交給 'scripts/colab_run.py'...")
        print("="*80)
        time.sleep(2)

        # 設定環境變數，將 Colab 參數傳遞給子程序
        env = os.environ.copy()
        env["LOG_DISPLAY_LINES"] = str(LOG_DISPLAY_LINES)
        env["LOG_ARCHIVE_FOLDER_NAME"] = str(LOG_ARCHIVE_FOLDER_NAME)
        env["TIMEZONE"] = str(TIMEZONE)
        env["REFRESH_RATE_SECONDS"] = str(REFRESH_RATE_SECONDS)
        env["PROJECT_PATH"] = str(project_path)
        env["BASE_PATH"] = str(base_path)

        # **關鍵修正**: 使用 subprocess.run 執行，而不是 import
        # 這可以確保 colab_run.py 在一個乾淨、已安裝好依賴的環境中以獨立程序運行
        core_script_path = project_path / "scripts" / "colab_run.py"
        if not core_script_path.exists():
            print(f"💥 致命錯誤：找不到核心腳本 '{core_script_path}'！")
        else:
            subprocess.run([sys.executable, str(core_script_path)], env=env, check=True)

    except subprocess.CalledProcessError as e:
        print(f"\n💥 執行外部命令時發生錯誤！")
        print(f"   命令: {' '.join(e.cmd)}")
        # 捕捉並解碼輸出
        stdout = e.stdout.strip() if hasattr(e, 'stdout') and e.stdout else ""
        stderr = e.stderr.strip() if hasattr(e, 'stderr') and e.stderr else ""
        if stdout: print(f"   輸出:\n{stdout}")
        if stderr: print(f"   錯誤訊息:\n{stderr}")
    except Exception as e:
        import traceback
        print(f"\n💥 啟動程序發生未預期的嚴重錯誤: {e}")
        traceback.print_exc()

# --- 執行啟動程序 ---
phoenix_bootstrap()
