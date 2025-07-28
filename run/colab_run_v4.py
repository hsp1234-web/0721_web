# coding: utf-8
# ╔═════════════════════════════════════════════════════════════════════════════╗
# ║                                                                             ║
# ║      🚀 鳳凰之心 Colab 整合啟動器 v6.0 (物件導向重構版)                     ║
# ║                                                                             ║
# ╠═════════════════════════════════════════════════════════════════════════════╣
# ║                                                                             ║
# ║ v6.0 更新 (Jules 重構):                                                     ║
# ║ - 物件導向設計: 將所有功能封裝至 `PhoenixLauncher` 類別，提高程式碼結      ║
# ║   構性、可讀性與可維護性。                                                  ║
# ║ - 集中化參數管理: 所有 Colab 表單參數在 `__init__` 中統一處理。           ║
# ║ - 清晰的日誌與輸出: 增加多種日誌等級（成功、失敗、警告、資訊）。            ║
# ║ - 穩健的錯誤處理: 透過 try...except...finally 確保流程的穩定性。          ║
# ║                                                                             ║
# ╚═════════════════════════════════════════════════════════════════════════════╝

# ====================================================================================
# Part 1: 參數設定區 (請在此處完成所有設定)
# ====================================================================================
#@title 💎 鳳凰之心指揮中心 (v6.0 物件導向版)
#@markdown ---
#@markdown ### 一、原始碼設定
#@markdown > 設定 Git 倉庫位址、要使用的版本 (分支或標籤)，以及專案在 Colab 中的資料夾名稱。
程式碼倉庫網址 = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
要使用的版本分支或標籤 = "3.1.0" #@param {type:"string"}
專案資料夾名稱 = "WEB" #@param {type:"string"}
#@markdown **強制刷新後端程式碼**
#@markdown >勾選此項會在本機刪除舊的專案資料夾，並從 Git 重新下載。
是否強制刷新程式碼 = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### 二、安裝與啟動設定
#@markdown > 選擇安裝模式、設定埠號，並決定是否執行啟動後測試。
安裝模式 = "完整安裝 (包含大型依賴)" #@param ["完整安裝 (包含大型依賴)", "模擬安裝 (僅核心依賴)"]
量化分析服務埠號 = 8001 #@param {type:"integer"}
語音轉寫服務埠號 = 8002 #@param {type:"integer"}
#@markdown **執行啟動後模擬測試 (Smoke Test)**
#@markdown >服務啟動後，會自動透過公開網址測試 API 連線，確保服務可從公網訪問。
是否執行啟動後測試 = True #@param {type:"boolean"}

#@markdown ---
#@markdown ### 三、日誌與時區設定
#@markdown > 設定日誌歸檔資料夾名稱和系統時區。
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
from io import StringIO
from IPython.display import display, Markdown, clear_output
import httpx
import nest_asyncio
import logging
class PhoenixLauncher:
    """
    鳳凰之心 Colab 整合啟動器
    將所有啟動邏輯封裝在此類別中，方便管理與維護。
    """
    # --- 靜態輔助類別與常數 ---
    class 色彩:
        標題 = '\033[95m'
        成功 = '\033[92m'
        警告 = '\033[93m'
        失敗 = '\033[91m'
        結束 = '\033[0m'
        粗體 = '\033[1m'

    def __init__(self, params):
        """
        初始化啟動器並設定所有參數。
        :param params: 一個包含所有從 Colab 表單獲取參數的字典。
        """
        # --- 從 params 字典解構參數 ---
        self.repo_url = params["程式碼倉庫網址"]
        self.repo_branch = params["要使用的版本分支或標籤"]
        self.project_folder = params["專案資料夾名稱"]
        self.force_refresh = params["是否強制刷新程式碼"]
        self.install_mode = params["安裝模式"]
        self.quant_port = params["量化分析服務埠號"]
        self.transcriber_port = params["語音轉寫服務埠號"]
        self.run_smoke_test = params["是否執行啟動後測試"]
        self.log_archive_folder = params["日誌歸檔資料夾"]
        self.timezone = params["時區"]

        # --- 動態與內部狀態設定 ---
        self.base_path = Path("/content") if Path("/content").exists() else Path.cwd()
        self.project_path = self.base_path / self.project_folder
        self.is_colab = "google.colab" in sys.modules
        self.launched_processes = []
        self.public_urls = {}
        self.timer_records = [("啟動", time.time())]
        self.full_log_capture = ""

    # --- 輸出與日誌輔助方法 ---
    def _setup_logging(self):
        """設定日誌系統，同時輸出到控制台和 StringIO。"""
        self.log_stream = StringIO()

        # 移除任何現有的處理器，以避免重複記錄
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # 設定日誌格式
        console_formatter = logging.Formatter('%(message)s')
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

        # 控制台處理器
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(console_formatter)

        # StringIO 處理器 (用於捕捉日誌以進行歸檔)
        stream_handler = logging.StreamHandler(self.log_stream)
        stream_handler.setFormatter(file_formatter)

        logging.basicConfig(level=logging.INFO, handlers=[console_handler, stream_handler])

    def _log(self, message, level="info"):
        """根據日誌等級記錄訊息。"""
        color_map = {
            "title": self.色彩.標題, "success": self.色彩.成功,
            "warning": self.色彩.警告, "error": self.色彩.失敗,
            "info": ""
        }
        icon_map = {
            "title": "🚀", "success": "✅", "warning": "⚠️",
            "error": "❌", "info": "ℹ️"
        }

        # 格式化訊息
        formatted_message = f"{icon_map.get(level, ' ')} {message}"
        if level == "title":
            formatted_message = f"\n{self.色彩.粗體}{formatted_message}{self.色彩.結束}"

        # 加上顏色
        full_message = f"{color_map.get(level, '')}{formatted_message}{self.色彩.結束}"

        # 根據等級使用 logging 模組
        if level == "error":
            logging.error(full_message)
        elif level == "warning":
            logging.warning(full_message)
        else:
            logging.info(full_message)

    def _timer_mark(self, name):
        """記錄一個時間點。"""
        self.timer_records.append((name, time.time()))

    def _generate_timer_report(self):
        """產生計時報告。"""
        report = "### ⏱️ 效能分析摘要\n\n| 階段 | 耗時 (秒) |\n| :--- | :--- |\n"
        for i in range(1, len(self.timer_records)):
            start_name, start_time = self.timer_records[i-1]
            end_name, end_time = self.timer_records[i]
            report += f"| {start_name} → {end_name} | {end_time - start_time:.2f} |\n"
        total_time = self.timer_records[-1][1] - self.timer_records[0][1]
        report += f"| **總計** | **{total_time:.2f}** |\n"
        return report


    def _execute_command(self, command, working_dir):
        """
        在指定目錄執行一個 shell 指令，並即時串流輸出。
        :return: (return_code, captured_output)
        """
        working_dir.mkdir(exist_ok=True, parents=True)
        self._log(f"在 '{working_dir}' 中執行: {self.色彩.粗體}{command}{self.色彩.結束}", level="info")

        process = subprocess.Popen(
            shlex.split(command),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            cwd=working_dir,
            text=True,
            encoding='utf-8',
            errors='replace'
        )

        output_lines = [f"--- {command} ---"]
        logging.info(f"--- {command} ---")

        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                clean_output = output.strip()
                logging.info(f"  {clean_output}")
                output_lines.append(clean_output)

        return_code = process.wait()
        if return_code != 0:
            self._log(f"指令 '{command}' 執行失敗，返回碼: {return_code}", level="error")

        return return_code, "\n".join(output_lines)

    # --- 主要執行流程的步驟 ---

    def _step_1_prepare_environment(self):
        """步驟 1: 準備腳本執行環境。"""
        self._log("步驟 1/6: 準備腳本執行環境", level="title")
        self._timer_mark("準備環境")
        # Colab 通常已內建，但在本地或某些環境可能需要
        cmd = f"{sys.executable} -m pip install -q httpx nest_asyncio"
        return_code, _ = self._execute_command(cmd, self.base_path)
        if return_code != 0:
            self._log("安裝核心腳本依賴 (httpx, nest_asyncio) 失敗！", level="error")
            return False
        self._log("核心腳本依賴已準備就緒。", level="success")
        return True

    def _step_2_prepare_project_code(self):
        """步驟 2: 準備專案程式碼。"""
        self._log("步驟 2/6: 準備專案程式碼", level="title")
        self._timer_mark("準備程式碼")

        if self.force_refresh and self.project_path.exists():
            self._log(f"偵測到強制刷新，正在移除舊的資料夾: {self.project_path}", level="info")
            shutil.rmtree(self.project_path)
            self._log("舊資料夾已移除。", level="success")

        if not self.project_path.exists():
            self._log("正在從 Git 下載專案程式碼...", level="info")
            command = f"git clone -q --branch {self.repo_branch} --depth 1 {self.repo_url} {self.project_path.name}"
            return_code, _ = self._execute_command(command, self.base_path)
            if return_code != 0:
                self._log("從 Git 下載程式碼失敗！", level="error")
                return False
            self._log("程式碼成功下載！", level="success")
        else:
            self._log("專案資料夾已存在，跳過下載。", level="info")

        # 切換工作目錄
        os.chdir(self.project_path)
        self._log(f"工作目錄已切換至: {os.getcwd()}", level="success")
        return True

    def _step_3_prepare_dependencies(self):
        """步驟 3: 準備依賴環境 (混合式)。"""
        self._log("步驟 3/6: 準備依賴環境 (混合式)", level="title")
        self._timer_mark("準備依賴")

        apps_dir = self.project_path / "apps"
        venvs_dir = Path(f"/dev/shm/{self.project_folder}_venvs") if sys.platform == "linux" else self.project_path / ".venvs"
        large_packages_dir = self.project_path / ".large_packages"
        install_large = "完整安裝" in self.install_mode

        try:
            subprocess.check_output(["uv", "--version"], stderr=subprocess.STDOUT)
        except (subprocess.CalledProcessError, FileNotFoundError):
            self._log("正在安裝 uv...", level="info")
            return_code, _ = self._execute_command(f"{sys.executable} -m pip install -q uv", self.project_path)
            if return_code != 0:
                self._log("安裝 uv 失敗！", level="error")
                return False

        if venvs_dir.exists():
            shutil.rmtree(venvs_dir)
        if large_packages_dir.exists():
            shutil.rmtree(large_packages_dir)

        venvs_dir.mkdir(parents=True, exist_ok=True)
        if install_large:
            large_packages_dir.mkdir(parents=True, exist_ok=True)

        for app_path in (d for d in apps_dir.iterdir() if d.is_dir()):
            app_name = app_path.name
            venv_path = venvs_dir / app_name
            python_executable = venv_path / 'bin/python'

            if self._execute_command(f"uv venv '{venv_path}' --seed", self.project_path)[0] != 0:
                return False

            req_file = app_path / "requirements.txt"
            if req_file.exists():
                if self._execute_command(f"uv pip install --python '{python_executable}' -r '{req_file}'", self.project_path)[0] != 0:
                    return False

            if install_large and (large_req_file := app_path / "requirements.large.txt").exists():
                target_dir = large_packages_dir / app_name
                target_dir.mkdir(exist_ok=True)
                if self._execute_command(f"uv pip install --target '{target_dir}' -r '{large_req_file}'", self.project_path)[0] != 0:
                    return False

        self._log("依賴環境已準備就緒。", level="success")
        return True

    def _step_4_launch_applications(self):
        """步驟 4: 啟動所有應用程式。"""
        self._log("步驟 4/6: 啟動所有應用程式", level="title")
        self._timer_mark("啟動應用")

        apps_dir = self.project_path / "apps"
        venvs_dir = Path(f"/dev/shm/{self.project_folder}_venvs") if sys.platform == "linux" else self.project_path / ".venvs"
        large_packages_dir = self.project_path / ".large_packages"
        install_large = "完整安裝" in self.install_mode

        app_ports = {"quant": self.quant_port, "transcriber": self.transcriber_port}

        for app_path in (d for d in apps_dir.iterdir() if d.is_dir()):
            app_name_raw = app_path.name
            app_name = app_name_raw.replace('_test', '')
            port = app_ports.get(app_name)

            if not port:
                continue

            venv_path = venvs_dir / app_name_raw
            python_executable = venv_path / 'bin/python'

            env = os.environ.copy()
            python_path_parts = [str(self.project_path)]

            if install_large and (p := large_packages_dir / app_name_raw).exists():
                python_path_parts.append(str(p))

            if (p_dir := next((venv_path / "lib").glob("python*"), None)) and (p_site := p_dir / "site-packages").exists():
                python_path_parts.append(str(p_site))

            env.update({
                "PYTHONPATH": os.pathsep.join(python_path_parts),
                "PORT": str(port),
                "TIMEZONE": self.timezone,
            })

            log_file = self.project_path / f"{app_name_raw}.log"

            process = subprocess.Popen(
                [str(python_executable), str(app_path / "main.py")],
                env=env,
                stdout=log_file.open('w'),
                stderr=subprocess.STDOUT
            )

            self.launched_processes.append(process)
            self._log(f"應用程式 '{app_name_raw}' (PID: {process.pid}) 已在背景啟動，日誌位於 {log_file}", level="success")

        return True

    def _step_5_generate_public_urls(self):
        """步驟 5: 生成 Colab 原生公開網址。"""
        self._log("步驟 5/6: 生成公開網址", level="title")
        self._timer_mark("生成網址")

        if not self.is_colab:
            self._log("非 Colab 環境，使用 localhost 作為網址。", level="warning")
            self.public_urls["量化分析服務"] = f"http://localhost:{self.quant_port}"
            self.public_urls["語音轉寫服務"] = f"http://localhost:{self.transcriber_port}"
        else:
            from google.colab.output import eval_js
            self.public_urls["量化分析服務"] = eval_js(f"google.colab.kernel.proxyPort({self.quant_port})")
            self.public_urls["語音轉寫服務"] = eval_js(f"google.colab.kernel.proxyPort({self.transcriber_port})")

        for name, url in self.public_urls.items():
            self._log(f"🌍 {name} 網址: {url}", level="success")

        return True
    async def _step_6_run_smoke_test(self):
        """步驟 6: 執行啟動後模擬測試 (Smoke Test)。"""
        self._log("步驟 6/6: 執行啟動後模擬測試", level="title")
        self._timer_mark("模擬測試")

        if not self.run_smoke_test:
            self._log("已跳過啟動後模擬測試。", level="warning")
            return True, "已跳過"

        self._log(f"等待 10 秒讓伺服器完全啟動...", level="info")
        await asyncio.sleep(10)

        results = []
        async with httpx.AsyncClient(timeout=30.0, verify=False) as client:
            for name, url in self.public_urls.items():
                test_url = url.rstrip('/') + "/docs"  # 通常是 API 文件的路徑
                try:
                    self._log(f"正在向 '{name}' 發送請求: GET {test_url}", level="info")
                    response = await client.get(test_url)

                    if 200 <= response.status_code < 500:
                        self._log(f"'{name}' 測試成功！服務可達，狀態碼: {response.status_code}", level="success")
                        results.append(True)
                    else:
                        self._log(f"'{name}' 測試失敗！伺服器錯誤，狀態碼: {response.status_code}", level="error")
                        results.append(False)

                except httpx.RequestError as e:
                    self._log(f"'{name}' 測試時發生網路錯誤: {e}", level="error")
                    results.append(False)

        all_passed = all(results)
        summary = f"{'✅ 全數通過' if all_passed else '❌ 部分失敗'} ({sum(results)}/{len(results)})"
        self._log(f"模擬測試完成: {summary}", level="success" if all_passed else "error")

        return all_passed, summary

    def _final_summary_and_archive(self, smoke_test_summary):
        """產生最終的 Markdown 摘要並歸檔日誌。"""
        self._timer_mark("完成")

        # --- 產生 Markdown 摘要 ---
        summary_report = f"## ✅ 鳳凰之心系統已成功啟動！\n\n"
        summary_report += f"**模擬測試結果**: **{smoke_test_summary}**\n\n"

        if self.launched_processes:
            pids = ', '.join(str(p.pid) for p in self.launched_processes)
            summary_report += f"**各服務正在背景運行中 (PIDs: {pids})**\n"

        for name, url in self.public_urls.items():
            summary_report += f"- **{name}**: [{url}]({url})\n"

        display(Markdown("---"), Markdown(summary_report))

        # --- 歸檔日誌 ---
        if self.log_archive_folder:
            archive_path = self.base_path / self.log_archive_folder
            archive_path.mkdir(exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            log_filename = archive_path / f"作戰日誌_{timestamp}.md"

            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_log = ansi_escape.sub('', self.full_log_capture)

            with log_filename.open("w", encoding="utf-8") as f:
                f.write(f"# 作戰日誌 {timestamp}\n\n")
                f.write("## 一、設定摘要\n")
                f.write(f"- **倉庫**: {self.repo_url} (版本: {self.repo_branch})\n")
                f.write(f"- **安裝模式**: {self.install_mode}\n\n")
                f.write(f"## 二、啟動總結\n{summary_report}\n")
                f.write(f"{self._generate_timer_report()}\n\n")
                f.write(f"## 三、詳細執行日誌\n```log\n{clean_log}\n```")

            self._log(f"本次作戰日誌已歸檔至: {log_filename}", level="success")

    def _cleanup_processes(self):
        """終止所有已啟動的背景程序。"""
        if not self.launched_processes:
            return

        self._log("正在嘗試關閉所有背景服務...", level="warning")
        for p in self.launched_processes:
            p.terminate() # 發送 SIGTERM

        # 等待一小段時間讓程序終止
        time.sleep(2)

        for p in self.launched_processes:
            if p.poll() is None: # 如果還在運行
                self._log(f"程序 PID {p.pid} 未能正常終止，強制終止 (SIGKILL)。", level="warning")
                p.kill() # 發送 SIGKILL

        self._log("所有背景服務已關閉。", level="success")

    async def _run_async_tasks(self):
        """執行所有需要非同步的任務。"""
        if not self._step_5_generate_public_urls(): return "生成網址失敗"
        _, smoke_test_summary = await self._step_6_run_smoke_test()
        return smoke_test_summary

    def _monitor_and_cleanup(self):
        """監控背景程序，並在收到中斷信號時進行清理。"""
        self._log("系統已啟動，進入監控模式。中斷執行 (Ctrl+C) 以關閉所有服務。", level="info")
        try:
            while True:
                for p in self.launched_processes:
                    if p.poll() is not None:
                        self._log(f"警告：偵測到進程 PID {p.pid} 已終止。請檢查日誌檔案。", level="warning")
                time.sleep(60)
        except KeyboardInterrupt:
            self._log("\n收到手動中斷信號 (Ctrl+C)。", level="warning")

    def run(self):
        """
        執行完整啟動流程的主方法。
        """
        # 清理先前輸出並設定日誌
        if self.is_colab:
            clear_output(wait=True)
        self._setup_logging()

        smoke_test_summary = "測試未執行"
        try:
            # --- 同步執行部分 ---
            if not self._step_1_prepare_environment(): return
            if not self._step_2_prepare_project_code(): return
            if not self._step_3_prepare_dependencies(): return
            if not self._step_4_launch_applications(): return

            # --- 非同步執行部分 ---
            nest_asyncio.apply()
            smoke_test_summary = asyncio.run(self._run_async_tasks())

            # --- 監控 ---
            self._monitor_and_cleanup()

        except KeyboardInterrupt:
            # 這個區塊現在由 _monitor_and_cleanup 內部處理
            pass

        except Exception as e:
            import traceback
            # 使用日誌記錄錯誤
            self._log(f"啟動過程中發生未預期的錯誤: {e}", level="error")
            # 記錄完整的追蹤資訊
            logging.error(traceback.format_exc())

        finally:
            self.full_log_capture = self.log_stream.getvalue()
            self._final_summary_and_archive(smoke_test_summary)
            self._cleanup_processes()
            self._log("鳳凰之心啟動器執行流程結束。", level="info")


# ====================================================================================
# Part 3: 執行啟動 (這是唯一的執行入口)
# ====================================================================================
if __name__ == "__main__":
    # 將 Colab 表單的參數打包成字典
    colab_params = {
        "程式碼倉庫網址": globals().get("程式碼倉庫網址", "https://github.com/hsp1234-web/0721_web"),
        "要使用的版本分支或標籤": globals().get("要使用的版本分支或標籤", "3.1.0"),
        "專案資料夾名稱": globals().get("專案資料夾名稱", "WEB"),
        "是否強制刷新程式碼": globals().get("是否強制刷新程式碼", True),
        "安裝模式": globals().get("安裝模式", "完整安裝 (包含大型依賴)"),
        "量化分析服務埠號": globals().get("量化分析服務埠號", 8001),
        "語音轉寫服務埠號": globals().get("語音轉寫服務埠號", 8002),
        "是否執行啟動後測試": globals().get("是否執行啟動後測試", True),
        "日誌歸檔資料夾": globals().get("日誌歸檔資料夾", "作戰日誌"),
        "時區": globals().get("時區", "Asia/Taipei"),
    }

    # 建立啟動器實例並執行
    launcher = PhoenixLauncher(colab_params)
    launcher.run()
