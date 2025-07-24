# 檔案: colab_bootstrap.py
# 說明: 此腳本為系統核心引擎，負責所有UI渲染與流程協調。

import argparse
import subprocess
import sys
import threading
import time
import psutil
import atexit
from pathlib import Path
from collections import deque
from IPython.display import display, update_display, HTML
from google.colab import output
from datetime import datetime

class DisplayManager:
    """管理 Colab 的動態顯示輸出。"""

    def __init__(self, log_lines=50, refresh_interval=0.2):
        self.log_lines = log_lines
        self.refresh_interval = refresh_interval
        self.log_queue = deque(maxlen=self.log_lines)
        self.status = {"cpu": 0, "ram": 0, "server_status": "PENDING"}
        self.iframe_html = ""
        self.display_id = f"phoenix-heart-{int(time.time() * 1e6)}"
        self.lock = threading.Lock()
        self._thread = None
        self._stop_event = threading.Event()

        self._initial_layout = f"""
        <style>
            #top-panel-{{display_id}}, #bottom-panel-{{display_id}} {{
                border: 1px solid #e0e0e0;
                padding: 10px;
                margin-bottom: 10px;
                border-radius: 8px;
                font-family: 'Roboto Mono', monospace;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            #log-container-{{display_id}} {{
                height: 300px;
                overflow-y: auto;
                background-color: #111;
                color: #eee;
                padding: 15px;
                border-radius: 4px;
                white-space: pre-wrap;
                word-wrap: break-word;
            }}
            .status-bar-{{display_id}} {{
                display: flex;
                justify-content: space-between;
                padding: 5px 0;
                font-size: 0.9em;
            }}
            .status-light-{{display_id}} {{
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }}
            .pending {{ background-color: #ffca28; }}
            .running {{ background-color: #66bb6a; }}
            .error {{ background-color: #ef5350; }}
        </style>
        <div id="top-panel-{self.display_id}">
            <h3>📊 整合式指揮中心</h3>
            <div class="status-bar-{self.display_id}">
                <span id="status-text-{self.display_id}">CPU: ... | RAM: ... | 伺服器: PENDING</span>
            </div>
            <h4>近期事件摘要</h4>
            <div id="log-container-{self.display_id}">正在初始化...</div>
        </div>
        <div id="bottom-panel-{self.display_id}">
            <!-- IFrame 將會顯示於此 -->
        </div>
        """
        display(HTML(self._initial_layout.replace("{display_id}", self.display_id)))

    def start(self):
        """在背景執行緒中啟動 UI 更新迴圈。"""
        self._thread = threading.Thread(target=self._update_loop, daemon=True)
        self._thread.start()

    def stop(self):
        """停止背景更新執行緒。"""
        self._stop_event.set()

    def update_log(self, message):
        """線程安全地新增日誌訊息。"""
        with self.lock:
            self.log_queue.append(message)

    def update_status(self, cpu, ram, server_status):
        """線程安全地更新系統狀態。"""
        with self.lock:
            self.status["cpu"] = cpu
            self.status["ram"] = ram
            self.status["server_status"] = server_status

    def render_iframe(self, url, port):
        """設定 IFrame 的內容。"""
        with self.lock:
            # 產生備用連結
            # 在真實的 Colab 環境中，我們會使用一個函式來獲取 URL
            # 為了本地測試的相容性，我們假設這個函式存在
            window_url = output.get_colab_url(port)
            self.iframe_html = f"""
            <p>✅ 您的應用程式已就緒！</p>
            <iframe src="{url}" width="100%" height="600px" frameborder="0"></iframe>
            <p>如果 iframe 無法載入，請嘗試 <a href="{window_url}" target="_blank">點此在新分頁中開啟</a>。</p>
            """

    def _update_loop(self):
        """主更新迴圈，定期刷新顯示內容。"""
        while not self._stop_event.is_set():
            with self.lock:
                # 組合日誌
                log_content = "<br>".join(self.log_queue)

                # 組合狀態
                server_status = self.status["server_status"].upper()
                status_color_class = server_status.lower()
                status_text = (
                    f'<span class="status-light-{self.display_id} {status_color_class}"></span>'
                    f'CPU: {self.status["cpu"]:.1f}% | '
                    f'RAM: {self.status["ram"]:.1f}% | '
                    f'伺服器: {server_status}'
                )

                # 組合最終 HTML
                update_html = f"""
                <script>
                    (function() {{
                        const logContainer = document.getElementById('log-container-{self.display_id}');
                        if (logContainer) {{
                            logContainer.innerHTML = `{log_content}`;
                            logContainer.scrollTop = logContainer.scrollHeight;
                        }}
                        const statusText = document.getElementById('status-text-{self.display_id}');
                        if (statusText) {{
                            statusText.innerHTML = `{status_text}`;
                        }}
                        const bottomPanel = document.getElementById('bottom-panel-{self.display_id}');
                        if (bottomPanel && bottomPanel.innerHTML.length === 0 && `{self.iframe_html}`.length > 0) {{
                             bottomPanel.innerHTML = `{self.iframe_html}`;
                        }}
                    }})();
                </script>
                """

            update_display(HTML(update_html), display_id=self.display_id)
            time.sleep(self.refresh_interval)

class LogManager:
    """管理日誌記錄、顯示與歸檔。"""

    def __init__(self, display_manager, archive_folder):
        self.display = display_manager
        self.archive_folder = Path(archive_folder)
        self.archive_folder.mkdir(exist_ok=True)
        self.full_log = []

    def _log(self, level, message):
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"[{timestamp}] [{level.upper()}] {message}"

        color_map = {
            "info": "#81d4fa",    # Light Blue
            "success": "#a5d6a7", # Light Green
            "warning": "#ffe082", # Light Yellow
            "error": "#ef9a9a",    # Light Red
            "fatal": "#f44336; font-weight: bold; color: white;" # Red
        }

        html_log_entry = f'<span style="color: {color_map.get(level, "#ffffff")};">{log_entry}</span>'

        self.display.update_log(html_log_entry)
        self.full_log.append(log_entry)

    def info(self, message):
        self._log("info", message)

    def success(self, message):
        self._log("success", message)

    def warning(self, message):
        self._log("warning", message)

    def error(self, message):
        self._log("error", message)

    def fatal(self, message):
        self._log("fatal", message)

    def archive_final_log(self):
        """將所有日誌寫入歸檔檔案。"""
        if not self.full_log:
            return

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_filename = self.archive_folder / f"phoenix_heart_combat_log_{timestamp}.txt"

        try:
            with open(log_filename, 'w', encoding='utf-8') as f:
                f.write("="*80 + "\n")
                f.write(f"作戰任務：鳳凰之心\n")
                f.write(f"歸檔時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n\n")
                f.write("\n".join(self.full_log))
            self.info(f"完整作戰日誌已歸檔至: {log_filename}")
        except Exception as e:
            self.error(f"歸檔日誌時發生錯誤: {e}")

# --- 全域子進程列表 ---
child_processes = []

def cleanup():
    """終止所有子進程。"""
    global child_processes
    for p in child_processes:
        if p.poll() is None: # 如果進程仍在執行
            try:
                # 使用 psutil 遞歸終止子進程
                parent = psutil.Process(p.pid)
                for child in parent.children(recursive=True):
                    child.kill()
                parent.kill()
            except psutil.NoSuchProcess:
                pass # 進程可能已經自己結束了
            except Exception as e:
                # 在此處我們無法使用 logger，因為它可能已經被銷毀
                print(f"清理子進程 {p.pid} 時發生錯誤: {e}", file=sys.stderr)
    child_processes = []

def monitor_stream(stream, logger_func):
    """從流中讀取數據並使用指定的 logger 函式記錄。"""
    try:
        for line in iter(stream.readline, ''):
            logger_func(line.strip())
        stream.close()
    except Exception:
        # 當進程終止時，流可能會被意外關閉
        pass

def main():
    # === 準備階段 ===
    parser = argparse.ArgumentParser(description="鳳凰之心 - 主推進引擎")
    parser.add_argument("--log-lines", type=int, default=50)
    parser.add_argument("--refresh-interval", type=float, default=0.2)
    parser.add_argument("--target-folder", type=str, required=True)
    parser.add_argument("--archive-folder", type=str, required=True)
    parser.add_argument("--port", type=int, required=True)
    args = parser.parse_args()

    display_manager = DisplayManager(args.log_lines, args.refresh_interval)
    log_manager = LogManager(display_manager, args.archive_folder)

    # 註冊清理函式
    atexit.register(cleanup)
    atexit.register(log_manager.archive_final_log)
    atexit.register(display_manager.stop)

    display_manager.start()
    log_manager.info("✅ 指揮中心引擎已啟動。")
    log_manager.info(f"日誌歸檔目錄設定為: {args.archive_folder}")

    server_process = None

    try:
        # === 作戰流程 ===
        # 1. **安裝依賴**
        log_manager.info("正在分析並安裝依賴套件 (uv_manager.py)...")
        uv_command = [sys.executable, "uv_manager.py", "--target-folder", args.target_folder]
        uv_process = subprocess.Popen(uv_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        child_processes.append(uv_process)

        # 非阻塞讀取輸出
        stdout_thread = threading.Thread(target=monitor_stream, args=(uv_process.stdout, log_manager.info))
        stderr_thread = threading.Thread(target=monitor_stream, args=(uv_process.stderr, log_manager.error))
        stdout_thread.start()
        stderr_thread.start()

        uv_process.wait() # 等待依賴安裝完成
        stdout_thread.join()
        stderr_thread.join()
        child_processes.remove(uv_process)

        if uv_process.returncode != 0:
            log_manager.fatal("❌ 依賴安裝失敗！返回碼非零。請檢查上方日誌。")
            return # 終止執行

        log_manager.success("✅ 所有依賴已成功安裝。")

        # 2. **啟動伺服器**
        log_manager.info("準備啟動後端伺服器 (run.py)...")
        server_command = [sys.executable, "run.py", "--port", str(args.port), "--app-dir", args.target_folder]
        server_process = subprocess.Popen(server_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        child_processes.append(server_process)

        # 非阻塞讀取伺服器輸出
        server_stdout_thread = threading.Thread(target=monitor_stream, args=(server_process.stdout, log_manager.info))
        server_stderr_thread = threading.Thread(target=monitor_stream, args=(server_process.stderr, log_manager.warning))
        server_stdout_thread.start()
        server_stderr_thread.start()

        log_manager.info(f"伺服器進程已啟動 (PID: {server_process.pid})。正在等待服務上線...")
        display_manager.update_status(0, 0, "STARTING")

        # 3. **監控與嵌入**
        server_ready = False
        # 使用 google.colab.output.get_colab_url 檢查埠號是否就緒
        for _ in range(60): # 最多等待60秒
            try:
                # 這個函式會在埠號可用時返回 URL，否則拋出異常
                iframe_url = output.get_colab_url(args.port, timeout_sec=1)
                log_manager.success(f"✅ 伺服器已在埠號 {args.port} 上線！")
                display_manager.render_iframe(iframe_url, args.port)
                display_manager.update_status(psutil.cpu_percent(), psutil.virtual_memory().percent, "RUNNING")
                server_ready = True
                break
            except Exception:
                time.sleep(1)

        if not server_ready:
            log_manager.fatal(f"❌ 伺服器未能在指定時間內於埠號 {args.port} 上啟動。")
            return

        # 4. **持續監控**
        while True:
            cpu_usage = psutil.cpu_percent()
            ram_usage = psutil.virtual_memory().percent

            if server_process.poll() is not None:
                log_manager.fatal("💥 伺服器進程意外終止！請檢查日誌以了解原因。")
                display_manager.update_status(cpu_usage, ram_usage, "ERROR")
                break

            display_manager.update_status(cpu_usage, ram_usage, "RUNNING")
            time.sleep(2) # 主監控迴圈的刷新率

    except KeyboardInterrupt:
        log_manager.warning("手动中斷指令已接收，開始執行清理程序...")
    except Exception as e:
        log_manager.fatal(f"發生未預期的致命錯誤: {e}")
    finally:
        log_manager.info("指揮中心引擎正在關閉...")
        if server_process and server_process.poll() is None:
             display_manager.update_status(psutil.cpu_percent(), psutil.virtual_memory().percent, "SHUTTING DOWN")
        # atexit 會自動呼叫 cleanup() 和 archive_final_log()

if __name__ == '__main__':
    main()
