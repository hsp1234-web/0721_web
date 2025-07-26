# ╔══════════════════════════════════════════════════════════════════╗
# ║                    🚀 colab_run.py 變更摘要 🚀                     ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                  ║
# ║  1. 新增日誌顯示行數控制：在 Part 2 新增 LOG_DISPLAY_LINES 參數， ║
# ║     讓您可以從表單直接設定要顯示的最新日誌行數，預設為 200。      ║
# ║                                                                  ║
# ║  2. 導入日誌緩衝與顯示核心：                                     ║
# ║     - 新增了 `log_buffer` (一個 collections.deque)，作為儲存日誌  ║
# ║       的先進先出緩衝區。                                         ║
# ║     - 新增了 `log_display_thread`，一個專門負責「清空畫面並重繪」  ║
# ║       日誌的獨立執行緒，徹底解決洗版問題。                       ║
# ║                                                                  ║
# ║  3. 重構日誌監聽器 `log_listener`：                               ║
# ║     - 此函式現在的職責很單純：接收後端傳來的日誌，並將其放入      ║
# ║       `log_buffer`，不再直接 print 到畫面上。                    ║
# ║                                                                  ║
# ║  4. 整合新的啟動流程：                                           ║
# ║     - 在主程序中啟動新的 `log_display_thread`，讓日誌的「接收」   ║
# ║       和「顯示」分離，實現高效穩定的監控面板效果。               ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心一鍵部署指揮中心 v31.0 (精準指示器版) { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼下載設定**
#@markdown > **設定您的 Git 倉庫、要下載的分支，以及存放程式碼的資料夾。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支 (TARGET_BRANCH)**
TARGET_BRANCH = "1.0.8" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **Part 2: 應用程式啟動設定**
#@markdown > **設定伺服器監聽的埠號與日誌顯示行數。**
#@markdown ---
#@markdown **後端服務埠號 (FASTAPI_PORT)**
FASTAPI_PORT = 8000 #@param {type:"integer"}
#@markdown **日誌顯示行數 (LOG_DISPLAY_LINES)**
#@markdown > 設定輸出面板中顯示的最新日誌行數。
LOG_DISPLAY_LINES = 200 #@param {type:"integer"}
#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
#           🚀 核心啟動器 (v31.0 - 精準指示器 & 日誌緩衝) 🚀
# ==============================================================================
import os
import sys
import shutil
import subprocess
import time
import threading
import collections
from pathlib import Path
from IPython.display import display, HTML, clear_output
from google.colab import output

# --- 核心改造: 日誌緩衝區與同步鎖 ---
# 使用 collections.deque 作為有固定長度的日誌緩衝區
# 當日誌數量超過 maxlen 時，最舊的日誌會被自動移除。
log_buffer = collections.deque(maxlen=LOG_DISPLAY_LINES)
# 執行緒鎖，用於確保多個執行緒在存取 log_buffer 時的資料安全
log_lock = threading.Lock()
# 停止事件，用於通知所有背景執行緒該結束了
stop_event = threading.Event()

# --- 核心改造: 日誌接收器 ---
# 這個函式會在背景執行緒中執行，專門負責從後端伺服器接收日誌。
# 它不再直接打印日誌，而是將日誌放入共享的 log_buffer 中。
def log_listener(pipe, pipe_name):
    """從指定的管道(pipe)讀取日誌，並將其加入到全域的 log_buffer。"""
    try:
        for line in iter(pipe.readline, b''):
            if stop_event.is_set():
                break
            # 獲取鎖，安全地將新日誌附加到緩衝區
            with log_lock:
                log_buffer.append(line.decode('utf-8').strip())
        pipe.close()
    except Exception as e:
        # 在主控台直接印出監聽器的錯誤，以便追蹤問題
        print(f"🚨 日誌監聽器發生錯誤 ({pipe_name}): {e}")

# --- 核心改造: 日誌顯示器 ---
# 這個函式是實現「不洗版」固定行數日誌面板的關鍵。
# 它會在一個獨立的背景執行緒中，以固定的頻率刷新畫面。
def log_display_thread(refresh_rate=0.5):
    """定期清空輸出並重繪日誌緩衝區中的所有內容。"""
    while not stop_event.is_set():
        # 清空儲存格輸出，wait=True 可防止閃爍
        clear_output(wait=True)

        # 打印標題
        print("🚀 鳳凰之心 v31.0 [精準指示器模式] 運行中...")
        print("="*80)
        print(f"面板將顯示最新的 {LOG_DISPLAY_LINES} 條日誌。所有完整日誌皆存於後端。")
        print("-"*80)

        # 獲取鎖，安全地複製當前的日誌內容並顯示
        with log_lock:
            # 直接在 Colab 輸出中印出緩衝區內的所有日誌
            for log_line in log_buffer:
                print(log_line)

        # 短暫睡眠，控制刷新頻率
        time.sleep(refresh_rate)

# ==============================================================================
# --- 執行流程開始 ---
# ==============================================================================
try:
    # --- 步驟 1/6: 準備環境與下載程式碼 ---
    clear_output(wait=True)
    print("🚀 鳳凰之心 v31.0 [精準指示器模式] 程序啟動...")
    print("="*80)
    print("\n--- 步驟 1/6: 準備環境與下載程式碼 ---")
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME
    print(f"ℹ️  目標專案資料夾路徑已設定為: {project_path}")

    if FORCE_REPO_REFRESH and project_path.exists():
        print(f"⚠️  偵測到「強制刷新」選項，正在刪除舊的資料夾: {project_path}")
        shutil.rmtree(project_path)
        print(f"✅  舊資料夾已成功移除。")

    if not project_path.exists():
        print(f"\n🚀 開始從 GitHub 拉取程式碼...")
        git_command = ["git", "clone", "--branch", TARGET_BRANCH, "--depth", "1", REPOSITORY_URL, str(project_path)]
        subprocess.run(git_command, check=True, capture_output=True, text=True, encoding='utf-8', cwd=base_path)
        print("\n✅ 程式碼成功下載並存放到指定資料夾！")
    else:
        print(f"✅  資料夾 '{project_path.name}' 已存在，跳過下載步驟。")

    # --- 步驟 2/6: 切換目錄 ---
    print("\n--- 步驟 2/6: 切換至專案目錄 ---")
    os.chdir(project_path)
    if str(project_path) not in sys.path:
        sys.path.insert(0, str(project_path))
    print(f"✅ 已成功切換至專案目錄: {project_path}")

    # --- 步驟 3/6: 安裝專案所需套件 ---
    print("\n--- 步驟 3/6: 安裝專案所需套件... ---")
    install_command = "pip install -q -r requirements/colab.txt"
    subprocess.run(install_command, shell=True, check=True)
    print("✅ 套件安裝完成。")

    # --- 步驟 4/6: 清理埠號 ---
    print(f"\n--- 步驟 4/6: 清理埠號 {FASTAPI_PORT}... ---")
    free_port_command = f"fuser -k -n tcp {FASTAPI_PORT}"
    subprocess.run(free_port_command, shell=True, capture_output=True)
    print(f"✅ 埠號 {FASTAPI_PORT} 已清理完畢。")

    # --- 步驟 5/6: 在背景啟動 FastAPI 與日誌監控 ---
    print("\n--- 步驟 5/6: 在背景啟動 FastAPI 與日誌監控... ---")
    server_env = os.environ.copy()
    server_env['PHOENIX_HEART_ROOT'] = str(project_path)

    server_process = subprocess.Popen(
        [sys.executable, "server_main.py"],
        env=server_env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    # 啟動日誌「接收」執行緒
    threading.Thread(target=log_listener, args=(server_process.stdout, 'SERVER_STDOUT'), daemon=True).start()
    threading.Thread(target=log_listener, args=(server_process.stderr, 'SERVER_STDERR'), daemon=True).start()

    # 啟動日誌「顯示」執行緒
    display_manager = threading.Thread(target=log_display_thread, daemon=True)
    display_manager.start()

    print("⏳ 等待伺服器初步啟動 (5秒)...")
    time.sleep(5)

    if server_process.poll() is not None:
        stop_event.set() # 如果伺服器啟動失敗，確保顯示執行緒也停止
        print(f"\n❌ 伺服器啟動失敗！請檢查日誌輸出。")
    else:
        print("\n✅ 伺服器已在背景成功啟動。")
        print("\n--- 步驟 6/6: 載入儀表板 ---")
        final_html = f"""
        <div style="border: 4px double #00ffdd; border-radius: 15px; padding: 10px; margin-top:20px; background-color:#0c0c1f;">
            <h2 style="color: #00ffdd; font-family: 'Orbitron', sans-serif; text-align: center;">
                🚀 鳳凰之心儀表板已上線 🚀
            </h2>
            <p style="color: #aafff0; font-family: 'Orbitron', sans-serif; text-align: center;">
                日誌面板已在上方運行，儀表板已成功嵌入下方。
            </p>
        </div>
        """
        display(HTML(final_html))
        output.serve_kernel_port_as_iframe(FASTAPI_PORT, height=800)

except Exception as e:
    import traceback
    stop_event.set() # 發生任何錯誤時，停止所有背景執行緒
    print(f"\n💥 執行期間發生未預期的嚴重錯誤: {e}")
    traceback.print_exc()

# 當儲存格執行完畢或被中斷時，這個區塊會被執行
finally:
    # 確保當 Colab 執行結束時，我們的背景執行緒也能優雅地停止
    if not stop_event.is_set():
        stop_event.set()
    # 給予執行緒一點時間來結束
    time.sleep(1)
    print("\n--- 指揮中心程序已停止 ---")
