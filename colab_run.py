
"""
鳳凰之心 v17.0 - Colab 即時反應駕駛艙
=======================================
此腳本為 Google Colab 環境的專用入口點，採用「介面優先」架構。

核心流程:
1.  **瞬間響應**: 立即渲染 HTML 駕駛艙介面，為使用者提供即時反饋。
2.  **後台執行**: 在獨立線程中處理所有耗時任務 (安裝依賴、啟動伺服器)。
3.  **即時串流**: 將安裝過程的每一行輸出即時串流到前端的「啟動畫面」。
4.  **無縫切換**: 任務完成後，自動將前端從「啟動畫面」切換為「主儀表板」，並開始推送即時系統狀態。
"""

import asyncio
import json
import logging
import os
import queue
import subprocess
import sys
import threading
import time
from pathlib import Path

# 確保在 Colab 環境中運行
try:
    from IPython import get_ipython
    from IPython.display import Javascript, display, HTML
    if 'google.colab' not in sys.modules:
        raise ImportError("Not in Google Colab")
except ImportError:
    print("❌ 致命錯誤：此腳本僅設計用於 Google Colab 環境。")
    sys.exit(1)

# --- 全域設定與日誌樣式 ---
LOG_LEVEL_STYLES = {
    'DEBUG': {'icon': '🐛', 'level': 'DEBUG'},
    'INFO': {'icon': '✨', 'level': 'INFO'},
    'WARNING': {'icon': '🟡', 'level': 'WARN'},
    'ERROR': {'icon': '🔴', 'level': 'ERROR'},
    'CRITICAL': {'icon': '🔥', 'level': 'CRITICAL'},
    'BATTLE': {'icon': '⚡', 'level': 'BATTLE'},
    'SUCCESS': {'icon': '✅', 'level': 'SUCCESS'},
    'SECURITY': {'icon': '🛡️', 'level': 'SECURITY'},
}

# --- 核心類別 ---

class UvicornLogHandler(logging.Handler):
    """攔截 uvicorn 日誌並將其格式化後放入佇列。"""
    def __init__(self, log_queue):
        super().__init__()
        self.log_queue = log_queue

    def emit(self, record):
        msg = record.getMessage()
        level = record.levelname
        
        # 忽略嘈雜的存取日誌，除非是錯誤
        if "GET /" in msg and record.status_code in [200, 304]:
            return
            
        log_entry = {
            "ts": time.strftime('%H:%M:%S'),
            "icon": LOG_LEVEL_STYLES.get(level, {}).get('icon', '📝'),
            "level": LOG_LEVEL_STYLES.get(level, {}).get('level', level),
            "msg": msg,
        }
        self.log_queue.put(log_entry)

class SystemMonitor:
    """監控系統資源 (CPU, RAM) 和服務進程。"""
    def __init__(self):
        self.psutil = None
        self.server_process = None

    def load_psutil(self):
        """延遲載入 psutil，並從虛擬環境中尋找。"""
        try:
            # 優先嘗試直接導入，以防它在全域可用
            import psutil
            self.psutil = psutil
            return True
        except ImportError:
            # 如果直接導入失敗，則嘗試從虛擬環境的 site-packages 中載入
            try:
                venv_dir = Path(".venv")
                # 這是一個常見的結構，但可能因 Python 版本而異
                site_packages = next(venv_dir.glob("lib/python*/site-packages"))
                if site_packages.is_dir() and str(site_packages) not in sys.path:
                    sys.path.insert(0, str(site_packages))

                import psutil
                self.psutil = psutil
                self._js_call('bootLog', '<span class="info">成功從 .venv 動態載入 psutil。</span>')
                return True
            except (StopIteration, ImportError) as e:
                self._js_call('bootLog', f'<span class="warn">⚠️ 無法找到或載入 psutil: {e}</span>')
                return False

    def start_server(self, port, log_queue):
        """在背景啟動 FastAPI 伺服器。"""
        env = os.environ.copy()
        env["PYTHONPATH"] = str(Path.cwd())
        # 使用虛擬環境的 python 來啟動伺服器
        cmd = [self.venv_python, "server_main.py", "--port", str(port)]
        
        self.server_process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding='utf-8', bufsize=1
        )

        # 為伺服器輸出建立一個監聽線程
        threading.Thread(target=self._log_server_output, args=(log_queue,), daemon=True).start()

    def _log_server_output(self, log_queue):
        """讀取伺服器進程的輸出並放入日誌佇列。"""
        for line in iter(self.server_process.stdout.readline, ''):
            log_entry = {
                "ts": time.strftime('%H:%M:%S'),
                "icon": "🚀", "level": "ENGINE",
                "msg": line.strip(),
            }
            log_queue.put(log_entry)

    def get_status(self):
        """獲取系統和服務的當前狀態。"""
        if not self.psutil:
            return {"cpu": 0, "ram": 0, "services": []}

        services = [
            {"name": "後端 FastAPI 引擎", "status": "ok" if self.server_process and self.server_process.poll() is None else "error"},
            {"name": "WebSocket 通訊頻道", "status": "ok"},
            {"name": "日誌資料庫", "status": "ok"},
        ]
        return {"cpu": self.psutil.cpu_percent(), "ram": self.psutil.virtual_memory().percent, "services": services}

    def stop_server(self):
        """停止伺服器進程。"""
        if self.server_process and self.server_process.poll() is None:
            self.server_process.terminate()
            try:
                self.server_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.server_process.kill()

class DashboardManager:
    """管理 HTML 儀表板的渲染和數據更新。"""
    def __init__(self, config):
        self.config = config
        self.log_queue = queue.Queue()
        self.monitor = SystemMonitor()
        self._stop_event = threading.Event()
        self.fastapi_url = f"http://127.0.0.1:{config['fastapi_port']}"

    def _js_call(self, function_name, *args):
        """輔助函數，用於安全地呼叫前端的 JavaScript 函數。"""
        try:
            json_args = [json.dumps(arg) for arg in args]
            js_code = f"window.{function_name}({', '.join(json_args)})"
            display(Javascript(js_code))
        except Exception:
            pass # 忽略在非活躍儲存格中的 JS 呼叫錯誤

    def _run_command(self, command, venv_path=None):
        """在子進程中執行命令並將輸出即時串流到前端。"""
        executable = command[0]
        if venv_path:
            executable = str(Path(venv_path) / "bin" / command[0])

        process = subprocess.Popen(
            [executable] + command[1:],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            bufsize=1
        )
        for line in iter(process.stdout.readline, ''):
            self._js_call('bootLog', f'<span class="dim">{line.strip()}</span>')

        process.wait()
        return process.returncode

    def _install_dependencies(self):
        """建立虛擬環境，安裝依賴，並通過 JS 顯示進度。"""
        self._js_call('bootLog', '<span class="header">&gt;&gt;&gt; 鳳凰之心 v17.0 駕駛艙啟動序列 &lt;&lt;&lt;</span>')
        
        venv_dir = Path(".venv")
        if not venv_dir.exists():
            self._js_call('bootLog', f'<span class="info">正在建立虛擬環境 (.venv)...</span>')
            try:
                subprocess.run([sys.executable, "-m", "venv", str(venv_dir)], check=True)
                self._js_call('bootLog', '<span class="ok">✅ 虛擬環境建立成功。</span>')
            except subprocess.CalledProcessError as e:
                self._js_call('bootLog', f'<span class="error">❌ 虛擬環境建立失敗: {e}</span>')
                return False
        else:
            self._js_call('bootLog', '<span class="info">偵測到現有虛擬環境 (.venv)，跳過建立步驟。</span>')
            
        # 定義虛擬環境中的執行檔路徑
        self.venv_python = str(venv_dir / "bin" / "python")
        self.venv_uv = str(venv_dir / "bin" / "uv")

        try:
            # 1. 在虛擬環境中安裝 uv
            self._js_call('bootLog', '<span class="info">在 .venv 中安裝 uv 加速器...</span>')
            if self._run_command([self.venv_python, "-m", "pip", "install", "-q", "uv"]) != 0:
                self._js_call('bootLog', f'<span class="error">❌ 在 .venv 中安裝 uv 失敗。</span>')
                return False

            # 2. 使用 venv 中的 uv 安裝依賴
            requirements_path = "requirements/colab.txt"
            self._js_call('bootLog', f'<span class="info">使用 .venv/bin/uv 安裝 {requirements_path}...</span>')
            
            return_code = self._run_command([self.venv_uv, "pip", "install", "-r", requirements_path])

            if return_code == 0:
                self._js_call('bootLog', '<span class="ok">✅ 所有依賴已成功安裝至 .venv。</span>')
                return True
            else:
                self._js_call('bootLog', f'<span class="error">❌ 依賴安裝失敗，返回碼: {return_code}</span>')
                return False
        except Exception as e:
            self._js_call('bootLog', f'<span class="error">❌ 安裝過程中發生嚴重錯誤: {e}</span>')
            return False

    def _work_thread_main(self):
        """在背景線程中執行的主工作流程。"""
        # 步驟 1: 安裝依賴
        if not self._install_dependencies():
            return

        # 步驟 2: 載入 psutil
        if not self.monitor.load_psutil():
            self._js_call('bootLog', '<span class="warn">⚠️ psutil 未能載入，資源監控將不可用。</span>')
        
        # 步驟 3: 啟動後端伺服器
        self._js_call('bootLog', '<span class="battle">⏳ 正在啟動後端 FastAPI 引擎...</span>')
        self.monitor.start_server(self.config['fastapi_port'], self.log_queue)
        time.sleep(4) # 給予伺服器啟動時間

        if self.monitor.server_process.poll() is not None:
            self._js_call('bootLog', '<span class="error">❌ 引擎啟動失敗，請檢查日誌。</span>')
            return
        
        self._js_call('bootLog', f'<span class="ok">✅ 引擎已上線: {self.fastapi_url}</span>')
        self._js_call('bootLog', '<span class="ok">✨ 系統啟動完成，歡迎指揮官。</span>')
        time.sleep(2)

        # 步驟 4: 啟動主更新迴圈
        self._update_loop()

    def _update_loop(self):
        """定期收集數據並推送到前端。"""
        while not self._stop_event.is_set():
            try:
                status_data = self.monitor.get_status()
                logs = []
                while not self.log_queue.empty():
                    logs.append(self.log_queue.get_nowait())
                
                full_data = {**status_data, "logs": logs, "fastapi_url": self.fastapi_url}
                self._js_call('updateDashboard', full_data)
                time.sleep(1)
            except Exception as e:
                error_log = {"ts": time.strftime('%H:%M:%S'), "icon": "🔥", "level": "CRITICAL", "msg": f"監控迴圈錯誤: {e}"}
                self._js_call('updateDashboard', {"logs": [error_log], "cpu":0, "ram":0, "services":[]})
                time.sleep(5)

    def run(self):
        """啟動儀表板的主流程。"""
        # 立即渲染 HTML 介面
        try:
            html_content = Path("templates/dashboard.html").read_text(encoding="utf-8")
            display(HTML(html_content))
        except FileNotFoundError:
            print("❌ 致命錯誤: 找不到 'templates/dashboard.html'。請確保檔案存在。")
            return
        
        time.sleep(1) # 等待 HTML 渲染

        # 在背景線程中執行所有耗時操作
        work_thread = threading.Thread(target=self._work_thread_main)
        work_thread.start()

        try:
            work_thread.join() # 等待工作線程自然結束或被中斷
        except KeyboardInterrupt:
            print("\n🛑 收到手動中斷信號，正在關閉系統...")
        finally:
            self.shutdown()

    def shutdown(self):
        """執行優雅的關閉程序。"""
        if not self._stop_event.is_set():
            self._stop_event.set()
            print("正在關閉監控...")
            self.monitor.stop_server()
            print("伺服器已停止。")

def main(config: dict):
    """ Colab 執行的主入口點。 """
    manager = DashboardManager(config)
    try:
        manager.run()
    except Exception as e:
        print(f"💥 儀表板管理器發生未預期的嚴重錯誤: {e}")
        import traceback
        traceback.print_exc()
    finally:
        manager.shutdown()
        print("\n✅ 系統已完全關閉。")


