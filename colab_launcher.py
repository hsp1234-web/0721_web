# -*- coding: utf-8 -*-
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║                                                                                 ║
# ║   🚀 鳳凰之心 Colab 整合啟動器 v3 (繁中終極版)                                  ║
# ║                                                                                 ║
# ╠═════════════════════════════════════════════════════════════════════════════╣
# ║                                                                                 ║
# ║   v3 更新 (Jules 全面升級):                                                     ║
# ║       - **極致中文體驗**: 所有參數、日誌、說明均採用繁體中文，清晰易懂。        ║
# ║       - **智慧日誌歸檔**: 自動將每次運行的完整日誌，包含效能分析，存檔為 .md。  ║
# ║       - **效能瓶頸分析**: 在歸檔日誌中自動生成各階段耗時報告，瓶頸一目了然。    ║
# ║       - **網址自動捕捉**: 執行後自動掃描服務日誌，捕獲並顯示 ngrok 等公網網址。 ║
# ║       - **整合 Git 流程**: 內建從零到一的完整流程，包含下載程式碼。             ║
# ║                                                                                 ║
# ╚═════════════════════════════════════════════════════════════════════════════╝

# ====================================================================================
# Part 1: 參數設定區 (請在此處完成所有設定)
# ====================================================================================
#@title 💎 鳳凰之心指揮中心 (v3 繁中終極版) { vertical-output: true, display-mode: "form" }

#@markdown ---
#@markdown ### **一、原始碼設定**
#@markdown > **設定 Git 倉庫位址、要使用的版本 (分支或標籤)，以及專案在 Colab 中的資料夾名稱。**
#@markdown ---
程式碼倉庫網址 = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
要使用的版本分支或標籤 = "main" #@param {type:"string"}
專案資料夾名稱 = "phoenix_project_v3" #@param {type:"string"}
#@markdown **強制刷新後端程式碼**
#@markdown >勾選此項會在本機刪除舊的專案資料夾，並從 Git 重新下載。
是否強制刷新程式碼 = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **二、安裝與啟動設定**
#@markdown > **選擇安裝模式，並為每個微服務應用指定啟動的埠號。**
#@markdown ---
安裝模式 = "模擬安裝 (僅核心依賴)" #@param ["完整安裝 (包含大型依賴)", "模擬安裝 (僅核心依賴)"]
量化分析服務埠號 = 8001 #@param {type:"integer"}
語音轉寫服務埠號 = 8002 #@param {type:"integer"}

#@markdown ---
#@markdown ### **三、日誌與時區設定**
#@markdown > **設定日誌歸檔資料夾名稱和系統時區。**
#@markdown ---
#@markdown **作戰日誌歸檔資料夾**
#@markdown > 所有本次執行的詳細過程，包含效能分析，都會存檔於此。留空則關閉此功能。
日誌歸檔資料夾 = "作戰日誌" #@param {type:"string"}
時區 = "Asia/Taipei" #@param {type:"string"}

# ====================================================================================
# Part 2: 核心啟動邏輯 (通常無需修改)
# ====================================================================================
import os
import sys
import subprocess
import shlex
import shutil
from pathlib import Path
import time
import re
from datetime import datetime
from IPython.display import display, Markdown

# --- 全域設定與輔助類別 ---
class 色彩:
    標題 = '\033[95m'
    成功 = '\033[92m'
    警告 = '\033[93m'
    失敗 = '\033[91m'
    結束 = '\033[0m'
    粗體 = '\033[1m'

class 計時器:
    def __init__(self):
        self.紀錄 = [("啟動", time.time())]
    def 標記(self, 名稱):
        self.紀錄.append((名稱, time.time()))
    def 產生報告(self):
        報告 = "### ⏱️ 效能分析摘要\n\n| 階段 | 耗時 (秒) |\n| :--- | :--- |\n"
        for i in range(1, len(self.紀錄)):
            階段名稱 = self.紀錄[i-1][0]
            耗時 = self.紀錄[i][1] - self.紀錄[i-1][1]
            報告 += f"| {階段名稱} | {耗時:.2f} |\n"
        總耗時 = self.紀錄[-1][1] - self.紀錄[0][1]
        報告 += f"| **總計** | **{總耗時:.2f}** |\n"
        return 報告

# --- 輔助函數 ---
def 印出標題(訊息): print(f"\n{色彩.標題}{色彩.粗體}🚀 {訊息} 🚀{色彩.結束}")
def 印出成功(訊息): print(f"{色彩.成功}✅ {訊息}{色彩.結束}")
def 印出警告(訊息): print(f"{色彩.警告}⚠️ {訊息}{色彩.結束}")
def 印出資訊(訊息): print(f"ℹ️ {訊息}")

def 執行指令(指令, 工作目錄, 環境變數=None):
    印出資訊(f"執行中: {色彩.粗體}{指令}{色彩.結束}")
    目前環境 = os.environ.copy()
    if 環境變數: 目前環境.update(環境變數)
    程序 = subprocess.Popen(
        shlex.split(指令), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=工作目錄, text=True, encoding='utf-8', errors='replace', env=目前環境
    )
    日誌輸出 = []
    while True:
        輸出 = 程序.stdout.readline()
        if 輸出 == '' and 程序.poll() is not None: break
        if 輸出:
            乾淨輸出 = 輸出.strip()
            print(f"   {乾淨輸出}")
            日誌輸出.append(乾淨輸出)
    返回碼 = 程序.wait()
    return 返回碼, 日誌輸出

# --- 主要功能函數 ---
def 準備專案程式碼(基礎路徑, 專案路徑, 計時):
    印出標題("步驟 1/4: 準備專案程式碼")
    if 是否強制刷新程式碼 and 專案路徑.exists():
        印出警告(f"偵測到「強制刷新」，正在刪除舊資料夾: {專案路徑}")
        shutil.rmtree(專案路徑)
        印出成功("舊資料夾已移除。")
    if not 專案路徑.exists():
        印出資訊(f"開始從 GitHub (版本: {要使用的版本分支或標籤}) 拉取程式碼...")
        指令 = f"git clone -q --branch {要使用的版本分支或標籤} --depth 1 {程式碼倉庫網址} {專案路徑.name}"
        返回碼, _ = 執行指令(指令, cwd=基礎路徑)
        if 返回碼 != 0:
            print(f"{色彩.失敗}Git clone 失敗！請檢查 URL 和分支/標籤名稱。{色彩.結束}")
            return False
        印出成功("程式碼成功下載！")
    else:
        印出成功(f"資料夾 '{專案路徑.name}' 已存在，跳過下載。")
    計時.標記("準備依賴環境")
    return True

def 準備依賴環境(專案路徑, 計時):
    印出標題("步驟 2/4: 準備依賴環境 (混合式)")
    應用程式目錄 = 專案路徑 / "apps"
    虛擬環境根目錄 = Path(f"/dev/shm/{專案資料夾名稱}_venvs") if sys.platform == "linux" else 專案路徑 / ".venvs"
    大型依賴根目錄 = 專案路徑 / ".large_packages"
    是否安裝大型依賴 = "完整安裝" in 安裝模式

    try:
        subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
    except (subprocess.CalledProcessError, FileNotFoundError):
        印出警告("uv 未找到，正在從 pip 安裝...")
        返回碼, _ = 執行指令(f"{sys.executable} -m pip install -q uv", cwd=專案路徑)
        if 返回碼 != 0: return False

    if 虛擬環境根目錄.exists(): shutil.rmtree(虛擬環境根目錄)
    if 大型依賴根目錄.exists(): shutil.rmtree(大型依賴根目錄)
    虛擬環境根目錄.mkdir(parents=True, exist_ok=True)
    if 是否安裝大型依賴: 大型依賴根目錄.mkdir(parents=True, exist_ok=True)

    印出資訊(f"虛擬環境根目錄: {虛擬環境根目錄}")
    if 是否安裝大型依賴: 印出資訊(f"大型依賴目錄: {大型依賴根目錄}")

    for 應用路徑 in (d for d in 應用程式目錄.iterdir() if d.is_dir()):
        應用名稱 = 應用路徑.name
        印出資訊(f"--- 正在準備 App: {應用名稱} ---")
        虛擬環境路徑 = 虛擬環境根目錄 / 應用名稱
        Python執行檔 = 虛擬環境路徑 / 'bin/python'

        返回碼, _ = 執行指令(f"uv venv '{虛擬環境路徑}' --seed", cwd=專案路徑)
        if 返回碼 != 0: return False

        需求檔案 = 應用路徑 / "requirements.txt"
        if 需求檔案.exists():
            返回碼, _ = 執行指令(f"uv pip install --python '{Python執行檔}' -r '{需求檔案}'", cwd=專案路徑)
            if 返回碼 != 0: return False

        大型需求檔案 = 應用路徑 / "requirements.large.txt"
        if 是否安裝大型依賴 and 大型需求檔案.exists():
            目標目錄 = 大型依賴根目錄 / 應用名稱
            目標目錄.mkdir(exist_ok=True)
            返回碼, _ = 執行指令(f"uv pip install --target '{目標目錄}' -r '{大型需求檔案}'", cwd=專案路徑)
            if 返回碼 != 0: return False

    印出成功("所有 App 環境均已準備就緒！")
    計時.標記("啟動應用程式")
    return True

def 啟動應用程式(專案路徑, 計時):
    印出標題("步驟 3/4: 啟動所有應用程式")
    應用程式目錄 = 專案路徑 / "apps"
    虛擬環境根目錄 = Path(f"/dev/shm/{專案資料夾名稱}_venvs") if sys.platform == "linux" else 專案路徑 / ".venvs"
    大型依賴根目錄 = 專案路徑 / ".large_packages"
    是否安裝大型依賴 = "完整安裝" in 安裝模式

    應用埠號 = {"quant": 量化分析服務埠號, "transcriber": 語音轉寫服務埠號}
    啟動的程序 = []

    for 應用路徑 in (d for d in 應用程式目錄.iterdir() if d.is_dir()):
        應用名稱 = 應用路徑.name
        埠號 = 應用埠號.get(應用名稱)
        if not 埠號: continue

        印出資訊(f"--- 正在啟動 App: {應用名稱} (埠號: {埠號}) ---")
        虛擬環境路徑 = 虛擬環境根目錄 / 應用名稱
        Python執行檔 = 虛擬環境路徑 / 'bin/python'
        主程式路徑 = 應用路徑 / "main.py"

        環境變數 = os.environ.copy()
        Python路徑列表 = [str(專案路徑)]

        if 是否安裝大型依賴:
            大型依賴路徑 = 大型依賴根目錄 / 應用名稱
            if 大型依賴路徑.exists(): Python路徑列表.append(str(大型依賴路徑))

        Python版本目錄 = next((虛擬環境路徑 / "lib").glob("python*"), None)
        if Python版本目錄 and (Python版本目錄 / "site-packages").exists():
            Python路徑列表.append(str(Python版本目錄 / "site-packages"))

        環境變數["PYTHONPATH"] = os.pathsep.join(Python路徑列表)
        環境變數["PORT"] = str(埠號)
        環境變數["TIMEZONE"] = 時區

        印出資訊(f"使用 PYTHONPATH: {環境變數['PYTHONPATH']}")

        日誌檔案 = Path(f"/content/{應用名稱}.log")
        印出資訊(f"日誌將輸出到: {日誌檔案}")

        程序 = subprocess.Popen(
            [str(Python執行檔), str(主程式路徑)], env=環境變數,
            stdout=日誌檔案.open('w'), stderr=subprocess.STDOUT
        )
        啟動的程序.append(程序)
        印出成功(f"App '{應用名稱}' 已在背景啟動，PID: {程序.pid}")

    計時.標記("完成啟動與掃描")
    return 啟動的程序

def 最終總結與網址掃描(啟動的程序, 計時):
    印出標題("步驟 4/4: 系統狀態總結與網址掃描")
    print("等待服務啟動以掃描日誌...")
    time.sleep(15) # 給服務 (特別是 ngrok) 一點時間啟動和寫入日誌

    公開網址 = {}
    網址正則 = re.compile(r"https?://[a-zA-Z0-9\-]+\.ngrok-free\.app")

    for app_name in ["quant", "transcriber"]:
        日誌檔案 = Path(f"/content/{app_name}.log")
        if 日誌檔案.exists():
            content = 日誌檔案.read_text()
            match = 網址正則.search(content)
            if match:
                url = match.group(0)
                公開網址[app_name] = url
                印出成功(f"在 '{app_name}' 的日誌中捕獲到網址: {url}")

    display(Markdown("---"))
    總結報告 = f"### ✅ 鳳凰之心系統已成功啟動！\n\n"
    總結報告 += f"**總耗時**: {計時.紀錄[-1][1] - 計時.紀錄[0][1]:.2f} 秒\n\n"
    總結報告 += f"**各服務正在背景運行中 (PIDs: {', '.join(str(p.pid) for p in 啟動的程序)})**\n"
    總結報告 += f"- **量化分析服務**: `http://localhost:{量化分析服務埠號}`\n"
    if "quant" in 公開網址:
        總結報告 += f"  - 🌍 **公網網址**: [{公開網址['quant']}]({公開網址['quant']})\n"
    總結報告 += f"- **語音轉寫服務**: `http://localhost:{語音轉寫服務埠號}`\n"
    if "transcriber" in 公開網址:
        總結報告 += f"  - 🌍 **公網網址**: [{公開網址['transcriber']}]({公開網址['transcriber']})\n"

    總結報告 += f"\n> **提示**: 日誌檔案位於 `/content/quant.log` 和 `/content/transcriber.log`。\n"
    總結報告 += "> 若要停止所有服務，請點擊 Colab 上方的「中斷執行」按鈕。"

    display(Markdown(總結報告))
    return 總結報告, 計時.產生報告()

# --- 主執行流程 ---
def main():
    計時器實例 = 計時器()

    # 捕獲所有輸出以供歸檔
    from io import StringIO
    import sys
    舊的_stdout = sys.stdout
    日誌串流 = StringIO()
    sys.stdout = 日誌串流

    try:
        from IPython.display import clear_output
        clear_output(wait=True)

        基礎路徑 = Path("/content")
        專案路徑 = 基礎路徑 / 專案資料夾名稱

        if not 準備專案程式碼(基礎路徑, 專案路徑, 計時器實例): return

        os.chdir(專案路徑)
        印出成功(f"工作目錄已切換至: {os.getcwd()}")

        if not 準備依賴環境(專案路徑, 計時器實例): return

        啟動的程序 = 啟動應用程式(專案路徑, 計時器實例)
        if not 啟動的程序:
            print(f"\n{色彩.失敗}❌ 未能啟動任何應用程式，啟動中止。{色彩.結束}")
            return

        # 恢復 stdout 以顯示最終報告
        sys.stdout = 舊的_stdout
        總結報告, 效能報告 = 最終總結與網址掃描(啟動的程序, 計時器實例)

        # 將捕獲的日誌寫回，讓使用者可以看到過程
        完整日誌 = 日誌串流.getvalue()
        print(完整日誌)

        # 處理日誌歸檔
        if 日誌歸檔資料夾:
            歸檔路徑 = 基礎路徑 / 日誌歸檔資料夾
            歸檔路徑.mkdir(exist_ok=True)
            時間戳 = datetime.now(datetime.strptime(時區, '%Z').tzinfo if sys.platform != 'win32' else None).strftime("%Y-%m-%d_%H-%M-%S")
            檔名 = 歸檔路徑 / f"作戰日誌_{時間戳}.md"

            # 清理 ANSI 顏色代碼
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            乾淨日誌 = ansi_escape.sub('', 完整日誌)

            with 檔名.open("w", encoding="utf-8") as f:
                f.write(f"# 鳳凰之心作戰日誌 - {時間戳}\n\n")
                f.write("## 一、系統設定摘要\n\n")
                f.write(f"- **倉庫網址**: {程式碼倉庫網址}\n")
                f.write(f"- **使用版本**: {要使用的版本分支或標籤}\n")
                f.write(f"- **安裝模式**: {安裝模式}\n\n")
                f.write(f"## 二、效能與總結\n\n")
                f.write(總結報告.replace("### ", "#### ") + "\n")
                f.write(效能報告 + "\n")
                f.write("## 三、詳細執行日誌\n\n")
                f.write("```log\n")
                f.write(乾淨日誌)
                f.write("\n```\n")
            print_success(f"本次作戰日誌已歸檔至: {檔名}")

        # 保持腳本運行
        while True: time.sleep(3600)

    except KeyboardInterrupt:
        sys.stdout = 舊的_stdout
        印出警告("\n收到手動中斷信號，正在關閉所有服務...")
        # 此處無法獲取 `啟動的程序` 變數，故提示使用者手動處理
        print("請注意：背景服務可能仍在運行。請透過 Colab 的「執行階段」->「中斷執行」來確保完全停止。")
    finally:
        sys.stdout = 舊的_stdout


if __name__ == "__main__":
    main()
