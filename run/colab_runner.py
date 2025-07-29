# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 Colab 動態儀表板執行器 v2.0                                     ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       遵循「不洗版」動態儀表板設計模式，在 Colab 輸出儲存格中         ║
# ║       直接渲染一個即時、高頻刷新的狀態儀表板，提供極致的使用者體驗。   ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心動態儀表板 v2.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "4.1.2" #@param {type:"string"}
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
TEST_MODE = "mock" #@param ["mock", "real"]

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心邏輯
# ==============================================================================
import os
import sys
import shutil
import subprocess
from pathlib import Path
import time
import threading

# --- 執行緒安全地執行核心任務 ---
def main_task(stats, log_manager):
    try:
        base_path = Path("/content")
        project_path = base_path / PROJECT_FOLDER_NAME

        # --- 步驟 1: 下載專案 ---
        stats['current_task'] = "下載專案程式碼..."
        stats['repo_status'] = "🟡 執行中..."
        log_manager.log("開始準備專案資料夾。")
        if FORCE_REPO_REFRESH and project_path.exists():
            log_manager.log(f"偵測到強制刷新，正在刪除舊資料夾: {project_path}", "WARN")
            shutil.rmtree(project_path)

        if not project_path.exists():
            log_manager.log(f"從 GitHub (分支/標籤: {TARGET_BRANCH_OR_TAG}) 拉取程式碼...")
            git_command = ["git", "clone", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", REPOSITORY_URL, str(project_path)]
            subprocess.run(git_command, check=True, capture_output=True, text=True, encoding='utf-8', cwd=base_path)
            log_manager.log("程式碼成功下載！")
        else:
            log_manager.log(f"資料夾 '{project_path.name}' 已存在，跳過下載。")
        stats['repo_status'] = "🟢 完成"
        os.chdir(project_path)
        log_manager.log(f"工作目錄已切換至: {os.getcwd()}")

        # --- 步驟 2: 安裝依賴 ---
        stats['current_task'] = "安裝核心依賴..."
        stats['deps_status'] = "🟡 執行中..."
        log_manager.log("安裝 psutil, pyyaml, uv...")
        # 移除 -q 參數以看到進度
        subprocess.run([sys.executable, "-m", "pip", "install", "psutil", "pyyaml", "uv", "nest_asyncio", "httpx"], check=True, capture_output=True, text=True)
        log_manager.log("核心依賴安裝完成。")
        stats['deps_status'] = "🟢 完成"

        # --- 步驟 3: E2E 測試 ---
        stats['current_task'] = f"以 '{TEST_MODE}' 模式執行端對端測試..."
        stats['test_status'] = "🟡 執行中..."
        log_manager.log(f"啟動 smart_e2e_test.py (模式: {TEST_MODE})")
        test_env = os.environ.copy()
        test_env["TEST_MODE"] = TEST_MODE
        result = subprocess.run(["python", "smart_e2e_test.py"], env=test_env, capture_output=True, text=True)

        for line in result.stdout.strip().split('\n'):
            log_manager.log(f"[E2E_TEST] {line}")
        if result.returncode != 0:
             for line in result.stderr.strip().split('\n'):
                log_manager.log(f"[E2E_TEST] {line}", "ERROR")
             raise RuntimeError("端對端測試失敗，請檢查日誌。")

        log_manager.log("端對端測試成功通過！")
        stats['test_status'] = "🟢 完成"

        # --- 步驟 4: 啟動後端服務 ---
        stats['current_task'] = "啟動後端服務..."
        stats['service_status'] = "🟡 執行中..."
        log_manager.log("匯入 nest_asyncio 並啟動 launch.py...")
        import nest_asyncio
        from multiprocessing import Process

        # 這裡我們不能直接 import launch，因為它會立即執行
        # 我們需要一種方式來在子進程中執行它
        def run_launcher_process():
            # 在子進程中，我們可以安全地 import 和執行
            from launch import main as launch_main
            import asyncio
            asyncio.run(launch_main())

        server_process = Process(target=run_launcher_process, daemon=True)
        server_process.start()
        log_manager.log("背景服務啟動程序已觸發。等待服務上線...")

        # 簡單的健康檢查
        time.sleep(20) # 給足夠的時間讓所有服務啟動
        proxy_url = "http://localhost:8000"
        import httpx
        response = httpx.get(proxy_url)
        if response.status_code == 200:
            log_manager.log("儀表板服務健康檢查通過！")
            stats['service_status'] = f"🟢 運行中 (點擊 {proxy_url} 訪問)"
            stats['current_task'] = "所有服務已就緒！"
        else:
            raise RuntimeError(f"服務健康檢查失敗，狀態碼: {response.status_code}")

    except Exception as e:
        log_manager.log(f"發生錯誤: {e}", "ERROR")
        # 更新所有失敗的狀態
        for key, value in stats.items():
            if value.endswith("執行中..."):
                stats[key] = "🔴 失敗"
        stats['current_task'] = "任務因錯誤而終止！"


# --- 啟動程序 ---
if __name__ == "__main__":
    # 延遲導入，確保在 Colab 環境中可用
    from core_utils.colab_display_manager import ColabDisplayManager
    from core_utils.colab_log_manager import ColabLogManager

    # 1. 初始化共享狀態物件
    shared_stats = {}
    log_manager = ColabLogManager()

    # 2. 初始化並啟動顯示管理器
    display_manager = ColabDisplayManager(shared_stats, log_manager)
    display_manager.start()

    # 3. 在主執行緒中執行核心任務
    main_task(shared_stats, log_manager)

    # 4. 停止顯示管理器並顯示最終畫面
    display_manager.stop()
