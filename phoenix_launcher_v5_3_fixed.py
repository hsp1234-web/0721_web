# -*- coding: utf-8 -*-
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║                                                                                 ║
# ║   🚀 鳳凰之心 Colab 整合啟動器 v5.3 (路徑修正 & 最終測試版)                   ║
# ║                                                                                 ║
# ╠═════════════════════════════════════════════════════════════════════════════╣
# ║                                                                                 ║
# ║   v5.3 更新 (Jules 最終修正):                                                   ║
# ║       - **路徑動態化**: 不再硬性依賴 `/content`，腳本會自動檢測並使用存在      ║
# ║         的路徑，使其在非 Colab 環境中也能順利執行模擬測試。                     ║
# ║       - **修正 TypeError**: 修正了 `執行指令` 函數的呼叫。                      ║
# ║       - **依賴自足**: 自動安裝腳本自身運行的 `IPython` 和 `httpx`。             ║
# ║                                                                                 ║
# ╚═════════════════════════════════════════════════════════════════════════════╝

# ====================================================================================
# Part 1: 參數設定區 (請在此處完成所有設定)
# ====================================================================================
#@title 💎 鳳凰之心指揮中心 (v5.3 最終修正版) { vertical-output: true, display-mode: "form" }

#@markdown ---
#@markdown ### **一、原始碼設定**
#@markdown > **設定 Git 倉庫位址、要使用的版本 (分支或標籤)，以及專案在 Colab 中的資料夾名稱。**
#@markdown ---
程式碼倉庫網址 = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
要使用的版本分支或標籤 = "3.1.0" #@param {type:"string"}
專案資料夾名稱 = "WEB" #@param {type:"string"}
#@markdown **強制刷新後端程式碼**
#@markdown >勾選此項會在本機刪除舊的專案資料夾，並從 Git 重新下載。
是否強制刷新程式碼 = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **二、安裝與啟動設定**
#@markdown > **選擇安裝模式、設定埠號，並決定是否執行啟動後測試。**
#@markdown ---
安裝模式 = "模擬安裝 (僅核心依賴)" #@param ["完整安裝 (包含大型依賴)", "模擬安裝 (僅核心依賴)"]
量化分析服務埠號 = 8001 #@param {type:"integer"}
語音轉寫服務埠號 = 8002 #@param {type:"integer"}
#@markdown **執行啟動後模擬測試 (Smoke Test)**
#@markdown >服務啟動後，會自動透過公開網址測試 API 連線，確保服務可從公網訪問。
是否執行啟動後測試 = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### **三、日誌與時區設定**
#@markdown > **設定日誌歸檔資料夾名稱和系統時區。**
#@markdown ---
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
import asyncio

# --- 全域設定與輔助類別 ---
class 色彩:
    標題 = '\033[95m'; 成功 = '\033[92m'; 警告 = '\033[93m'; 失敗 = '\033[91m'
    結束 = '\033[0m'; 粗體 = '\033[1m'

class 計時器:
    def __init__(self): self.紀錄 = [("啟動", time.time())]
    def 標記(self, 名稱): self.紀錄.append((名稱, time.time()))
    def 產生報告(self):
        報告 = "### ⏱️ 效能分析摘要\n\n| 階段 | 耗時 (秒) |\n| :--- | :--- |\n"
        for i in range(1, len(self.紀錄)):
            報告 += f"| {self.紀錄[i-1][0]} | {self.紀錄[i][1] - self.紀錄[i-1][1]:.2f} |\n"
        報告 += f"| **總計** | **{self.紀錄[-1][1] - self.紀錄[0][1]:.2f}** |\n"
        return 報告

# --- 輔助函數 ---
def 印出標題(訊息): print(f"\n{色彩.標題}{色彩.粗體}🚀 {訊息} 🚀{色彩.結束}")
def 印出成功(訊息): print(f"{色彩.成功}✅ {訊息}{色彩.結束}")
def 印出警告(訊息): print(f"{色彩.警告}⚠️ {訊息}{色彩.結束}")
def 印出資訊(訊息): print(f"ℹ️ {訊息}")

def 執行指令(指令, 工作目錄):
    工作目錄.mkdir(exist_ok=True, parents=True) # 確保工作目錄存在
    印出資訊(f"在 '{工作目錄}' 中執行: {色彩.粗體}{指令}{色彩.結束}")
    程序 = subprocess.Popen(
        shlex.split(指令), stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        cwd=工作目錄, text=True, encoding='utf-8', errors='replace'
    )
    日誌輸出 = [f"--- {指令} ---"]; print(f"   --- {指令} ---")
    while True:
        輸出 = 程序.stdout.readline()
        if 輸出 == '' and 程序.poll() is not None: break
        if 輸出:
            乾淨輸出 = 輸出.strip()
            print(f"   {乾淨輸出}"); 日誌輸出.append(乾淨輸出)
    return 程序.wait(), 日誌輸出

# --- 主要功能函數 ---
def 準備執行環境(基礎路徑, 計時):
    印出標題("步驟 1/6: 準備腳本執行環境")
    # 增加 nest_asyncio 以解決 Colab 中的 asyncio.run() 問題
    返回碼, _ = 執行指令(f"{sys.executable} -m pip install -q IPython httpx nest_asyncio", 基礎路徑)
    if 返回碼 != 0:
        印出失敗("安裝核心腳本依賴 (IPython, httpx, nest_asyncio) 失敗！")
        return False
    印出成功("核心腳本依賴已準備就緒。")
    計時.標記("準備專案程式碼")
    return True

def 準備專案程式碼(基礎路徑, 專案路徑, 計時):
    印出標題("步驟 2/6: 準備專案程式碼")
    if 是否強制刷新程式碼 and 專案路徑.exists():
        shutil.rmtree(專案路徑); 印出成功("舊資料夾已移除。")
    if not 專案路徑.exists():
        指令 = f"git clone -q --branch {要使用的版本分支或標籤} --depth 1 {程式碼倉庫網址} {專案路徑.name}"
        返回碼, _ = 執行指令(指令, 基礎路徑)
        if 返回碼 != 0: return False
        印出成功("程式碼成功下載！")
    計時.標記("準備依賴環境")
    return True

def 準備依賴環境(專案路徑, 計時):
    印出標題("步驟 3/6: 準備依賴環境 (混合式)")
    應用程式目錄 = 專案路徑 / "apps"; 虛擬環境根目錄 = Path(f"/dev/shm/{專案資料夾名稱}_venvs") if sys.platform == "linux" else 專案路徑 / ".venvs"
    大型依賴根目錄 = 專案路徑 / ".large_packages"; 是否安裝大型依賴 = "完整安裝" in 安裝模式
    try: subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
    except:
        返回碼, _ = 執行指令(f"{sys.executable} -m pip install -q uv", 專案路徑)
        if 返回碼 != 0: return False
    if 虛擬環境根目錄.exists(): shutil.rmtree(虛擬環境根目錄)
    if 大型依賴根目錄.exists(): shutil.rmtree(大型依賴根目錄)
    虛擬環境根目錄.mkdir(parents=True, exist_ok=True)
    if 是否安裝大型依賴: 大型依賴根目錄.mkdir(parents=True, exist_ok=True)
    for 應用路徑 in (d for d in 應用程式目錄.iterdir() if d.is_dir()):
        應用名稱 = 應用路徑.name; 虛擬環境路徑 = 虛擬環境根目錄 / 應用名稱
        Python執行檔 = 虛擬環境路徑 / 'bin/python'
        if 執行指令(f"uv venv '{虛擬環境路徑}' --seed", 專案路徑)[0] != 0: return False
        if (p := 應用路徑 / "requirements.txt").exists() and 執行指令(f"uv pip install --python '{Python執行檔}' -r '{p}'", 專案路徑)[0] != 0: return False
        if 是否安裝大型依賴 and (p := 應用路徑 / "requirements.large.txt").exists():
            目標目錄 = 大型依賴根目錄 / 應用名稱; 目標目錄.mkdir(exist_ok=True)
            if 執行指令(f"uv pip install --target '{目標目錄}' -r '{p}'", 專案路徑)[0] != 0: return False
    計時.標記("啟動應用程式")
    return True

def 啟動應用程式(專案路徑, 計時):
    印出標題("步驟 4/6: 啟動所有應用程式")
    應用程式目錄 = 專案路徑 / "apps"; 虛擬環境根目錄 = Path(f"/dev/shm/{專案資料夾名稱}_venvs") if sys.platform == "linux" else 專案路徑 / ".venvs"
    大型依賴根目錄 = 專案路徑 / ".large_packages"; 是否安裝大型依賴 = "完整安裝" in 安裝模式
    應用埠號 = {"quant": 量化分析服務埠號, "transcriber": 語音轉寫服務埠號}; 啟動的程序 = []
    for 應用路徑 in (d for d in 應用程式目錄.iterdir() if d.is_dir()):
        應用名稱 = 應用路徑.name.replace('_test', ''); 埠號 = 應用埠號.get(應用名稱) # 移除 _test 以匹配
        if not 埠號: continue
        虛擬環境路徑 = 虛擬環境根目錄 / 應用路徑.name; Python執行檔 = 虛擬環境路徑 / 'bin/python'
        環境變數 = os.environ.copy(); Python路徑列表 = [str(專案路徑)]
        if 是否安裝大型依賴 and (p := 大型依賴根目錄 / 應用路徑.name).exists(): Python路徑列表.append(str(p))
        if (p_dir := next((虛擬環境路徑 / "lib").glob("python*"), None)) and (p_site := p_dir / "site-packages").exists(): Python路徑列表.append(str(p_site))
        環境變數.update({"PYTHONPATH": os.pathsep.join(Python路徑列表), "PORT": str(埠號), "TIMEZONE": 時區})
        日誌檔案 = Path(f"./{應用路徑.name}.log")
        程序 = subprocess.Popen([str(Python執行檔), str(應用路徑 / "main.py")], env=環境變數, stdout=日誌檔案.open('w'), stderr=subprocess.STDOUT)
        啟動的程序.append(程序); 印出成功(f"App '{應用路徑.name}' (PID: {程序.pid}) 已在背景啟動，日誌位於 {日誌檔案}")
    計時.標記("生成公開網址")
    return 啟動的程序

def 生成並顯示網址(計時):
    印出標題("步驟 5/6: 生成 Colab 原生公開網址")
    try:
        from google.colab.output import eval_js
        is_colab = True
    except ImportError:
        is_colab = False

    公開網址 = {}
    for 名稱, 埠號 in [("量化分析服務", 量化分析服務埠號), ("語音轉寫服務", 語音轉寫服務埠號)]:
        if is_colab:
            url = eval_js(f"google.colab.kernel.proxyPort({埠號})")
        else:
            url = f"http://localhost:{埠號}"
        公開網址[名稱] = url
        印出成功(f"🌍 {名稱} 網址: {url}")

    計時.標記("執行啟動後模擬測試")
    return 公開網址

async def 執行模擬測試(公開網址, 計時):
    印出標題("步驟 6/6: 執行啟動後模擬測試 (Smoke Test)")
    if not 是否執行啟動後測試:
        印出警告("已跳過啟動後模擬測試。"); 計時.標記("完成")
        return True, "已跳過"

    import httpx
    結果 = []; 印出資訊("等待 10 秒讓伺服器完全啟動..."); await asyncio.sleep(10)
    async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
        for 名稱, url in 公開網址.items():
            測試路徑 = url.rstrip('/') + "/docs"
            try:
                印出資訊(f"正在向 '{名稱}' 發送請求: GET {測試路徑}")
                回應 = await client.get(測試路徑)
                if 200 <= 回應.status_code < 500:
                    印出成功(f"'{名稱}' 測試成功！服務可達，狀態碼: {回應.status_code}"); 結果.append(True)
                else:
                    印出失敗(f"'{名稱}' 測試失敗！伺服器錯誤，狀態碼: {回應.status_code}"); 結果.append(False)
            except httpx.RequestError as e:
                印出失敗(f"'{名稱}' 測試時發生網路錯誤: {e}"); 結果.append(False)

    計時.標記("完成"); 全部成功 = all(結果)
    return 全部成功, f"{'✅ 全數通過' if 全部成功 else '❌ 部分失敗'} ({sum(結果)}/{len(結果)})"

# --- 主執行流程 ---
async def run_async_tasks(公開網址, 計時器實例, 完整日誌_過程):
    """執行所有需要非同步操作的任務，例如 API 測試。"""
    from io import StringIO
    from IPython.display import display, Markdown

    舊的_stdout = sys.stdout
    日誌串流 = StringIO()
    sys.stdout = 日誌串流

    測試結果, 測試摘要 = await 執行模擬測試(公開網址, 計時器實例)

    sys.stdout = 舊的_stdout
    完整日誌_測試 = 日誌串流.getvalue()
    print(完整日誌_測試)

    return 測試結果, 測試摘要, 完整日誌_測試

def main_sync():
    """程式主進入點，協調同步與非同步任務。"""
    計時器實例 = 計時器()
    基礎路徑 = Path("/content") if Path("/content").exists() else Path.cwd()

    # --- Part 1: 同步執行所有準備工作 ---
    if not 準備執行環境(基礎路徑, 計時器實例): return

    from io import StringIO
    from IPython.display import display, Markdown

    # 清理 Colab 輸出
    try:
        from IPython.display import clear_output
        clear_output(wait=True)
    except ImportError:
        pass

    # 為了捕捉過程日誌，我們暫時重定向 stdout
    舊的_stdout = sys.stdout
    日誌串流 = StringIO()
    sys.stdout = 日誌串流

    專案路徑 = 基礎路徑 / 專案資料夾名稱
    if not 準備專案程式碼(基礎路徑, 專案路徑, 計時器實例):
        sys.stdout = 舊的_stdout
        print(日誌串流.getvalue())
        return

    os.chdir(專案路徑)
    印出成功(f"工作目錄已切換至: {os.getcwd()}")

    if not 準備依賴環境(專案路徑, 計時器實例):
        sys.stdout = 舊的_stdout
        print(日誌串流.getvalue())
        return

    啟動的程序 = 啟動應用程式(專案路徑, 計時器實例)
    if not 啟動的程序:
        sys.stdout = 舊的_stdout
        print(日誌串流.getvalue())
        return

    # 恢復 stdout，並印出至今為止的日誌
    sys.stdout = 舊的_stdout
    完整日誌_過程 = 日誌串流.getvalue()
    print(完整日誌_過程)

    # --- Part 2: 執行網址生成與非同步測試 ---
    公開網址 = 生成並顯示網址(計時器實例)

    # 安全地執行非同步任務
    import nest_asyncio
    nest_asyncio.apply()
    測試結果, 測試摘要, 完整日誌_測試 = asyncio.run(run_async_tasks(公開網址, 計時器實例, 完整日誌_過程))

    # --- Part 3: 產生最終報告並歸檔 ---
    總結報告 = f"### ✅ 鳳凰之心系統已成功啟動！\n\n**模擬測試結果**: **{測試摘要}**\n\n**各服務正在背景運行中 (PIDs: {', '.join(str(p.pid) for p in 啟動的程序)})**\n"
    for 名稱, url in 公開網址.items():
        總結報告 += f"- **{名稱}**: [{url}]({url})\n"
    display(Markdown("---"), Markdown(總結報告))

    if 日誌歸檔資料夾:
        歸檔路徑 = 基礎路徑 / 日誌歸檔資料夾
        歸檔路徑.mkdir(exist_ok=True)
        時間戳 = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        檔名 = 歸檔路徑 / f"作戰日誌_{時間戳}.md"
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        with 檔名.open("w", encoding="utf-8") as f:
            f.write(f"# 作戰日誌 {時間戳}\n\n## 一、設定摘要\n- **倉庫**: {程式碼倉庫網址} (版本: {要使用的版本分支或標籤})\n- **安裝模式**: {安裝模式}\n\n")
            f.write(f"## 二、啟動總結\n{總結報告}\n\n{計時器實例.產生報告()}\n\n")
            f.write(f"## 三、詳細執行日誌\n```log\n{ansi_escape.sub('', 完整日誌_過程 + 完整日誌_測試)}\n```")
        印出成功(f"本次作戰日誌已歸檔至: {檔名}")

    # --- Part 4: 保持 Colab 儲存格活躍 ---
    印出資訊("系統已啟動，進入監控模式。中斷執行 (Ctrl+C) 以關閉所有服務。")
    try:
        while True:
            for p in 啟動的程序:
                if p.poll() is not None:
                    印出警告(f"警告：偵測到進程 PID {p.pid} 已終止。請檢查日誌檔案。")
            time.sleep(60)
    except KeyboardInterrupt:
        印出警告("\n收到手動中斷信號，正在嘗試關閉所有背景服務...")
        for p in 啟動的程序:
            p.terminate()
        # 等待一小段時間讓程序終止
        time.sleep(2)
        for p in 啟動的程序:
            if p.poll() is None: # 如果還在運行
                p.kill() # 強制終止
        印出成功("所有背景服務已關閉。")
    except Exception as e:
        import traceback
        traceback.print_exc()
    finally:
        印出成功("鳳凰之心啟動器已結束。")

if __name__ == "__main__":
    main_sync()
