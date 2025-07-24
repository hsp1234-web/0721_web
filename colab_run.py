# -*- coding: utf-8 -*-
# 最終作戰計畫 P8：鳳凰之心
# Colab 儀表板 (colab_run.py) v3.0.0

import html
import os
import sys
import threading
import time
import sqlite3
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

# 只有在 Colab 環境中才導入這些模組
try:
    from IPython.display import display, HTML, Javascript
    from google.colab import output as colab_output
except ImportError:
    print("🔴 [錯誤] 此腳本設計為在 Google Colab 環境中運行。缺少必要的 Colab API。")
    # 如果不在 Colab 中，定義虛擬函式以避免啟動時出錯
    def display(*args, **kwargs): pass
    def HTML(s): return s
    def Javascript(s): return s
    class MockColabOutput:
        def serve_kernel_port_as_iframe(self, *args, **kwargs): pass
        def redirect_to_element(self, *args, **kwargs): return self
        def __enter__(self): pass
        def __exit__(self, exc_type, exc_val, exc_tb): pass
    colab_output = MockColabOutput()


# --- 全域常數 ---
LOG_DISPLAY_LINES = 50
STATUS_REFRESH_INTERVAL = 1.0
DB_PATH = Path("logs.sqlite")
STOP_EVENT = threading.Event()

# --- 顯示管理器 (UI Thread) ---
class DisplayManager(threading.Thread):
    """在獨立線程中，持續從資料庫讀取日誌並更新 Colab UI。"""
    def __init__(self, db_path, stop_event):
        super().__init__(daemon=True)
        self.db_path = db_path
        self.stop_event = stop_event
        self.last_log_id = 0
        self.last_status_update = 0
        self.taipei_tz = ZoneInfo("Asia/Taipei")
        self.is_ui_setup = False

    def _execute_js(self, js_code):
        try:
            display(Javascript(js_code))
        except Exception:
            # 在 Colab 環境中，如果 JS 執行失敗，通常是前端尚未準備好
            pass

    def setup_ui(self):
        from IPython.display import clear_output
        clear_output(wait=True)
        ui_html = f"""
        <style>
            .grid-container {{ display: grid; grid-template-columns: 10ch 11ch 1fr; gap: 0 8px; font-family: 'Fira Code', 'Consolas', monospace; font-size: 13px; line-height: 1.6; }}
            .grid-item {{ white-space: pre; }}
            #status-bar {{ margin-top: 10px; border-top: 1px solid #444; padding-top: 4px; }}
            #portal-container {{ margin-bottom: 15px; }}
            .version-tag {{ font-weight: bold; color: #757575; margin-left: 12px; }}
        </style>
        <div id="portal-container"></div>
        <div id="log-panel" class="grid-container"></div>
        <div id="status-bar" class="grid-container"></div>
        """
        display(HTML(ui_html))
        self.is_ui_setup = True

    def _update_status_bar(self):
        now = time.time()
        if now - self.last_status_update < STATUS_REFRESH_INTERVAL:
            return
        self.last_status_update = now

        try:
            # 延遲導入 psutil，因為它是由 poetry 安裝的
            import psutil
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            time_str = datetime.now(self.taipei_tz).strftime('%H:%M:%S')

            # 從資料庫獲取最新版本號
            version = "N/A"
            if self.db_path.exists():
                with sqlite3.connect(self.db_path) as conn:
                    result = conn.execute("SELECT version FROM logs ORDER BY id DESC LIMIT 1").fetchone()
                    if result: version = result[0]

            status_html = (
                f"<div class='grid-item' style='color: #FFFFFF;'>{time_str}</div>"
                f"<div class='grid-item' style='color: #FFFFFF;'>| CPU: {cpu:4.1f}%</div>"
                f"<div class='grid-item' style='color: #FFFFFF;'>| RAM: {ram:4.1f}% | [系統運行中 <span class='version-tag'>{version}</span>]</div>"
            )
            escaped_status_html = status_html.replace('`', '\\`')
            js_code = f"document.getElementById('status-bar').innerHTML = `{escaped_status_html}`;"
            self._execute_js(js_code)
        except (ImportError, Exception):
             # 啟動初期 psutil 可能尚未安裝，或資料庫尚未建立，忽略錯誤
            pass

    def _update_log_panel(self):
        if not self.db_path.exists(): return
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                new_logs = conn.execute("SELECT * FROM logs WHERE id > ? ORDER BY id ASC", (self.last_log_id,)).fetchall()

            if not new_logs: return

            for log in new_logs:
                formatted_ts = datetime.fromisoformat(log['timestamp']).strftime('%H:%M:%S')
                level_upper = log['level'].upper()
                colors = {"SUCCESS": '#4CAF50', "ERROR": '#F44336', "CRITICAL": '#F44336', "WARNING": '#FBC02D', "INFO": '#B0BEC5'}
                level_color = colors.get(level_upper, '#B0BEC5')

                log_html = (
                    f"<div class='grid-item' style='color: #FFFFFF;'>[{formatted_ts}]</div>"
                    f"<div class='grid-item' style='color: {level_color}; font-weight: bold;'>[{level_upper:<8}]</div>"
                    f"<div class='grid-item' style='color: #FFFFFF;'>[{log['version']}] {html.escape(log['message'])}</div>"
                )

                js_code = f"""
                const panel = document.getElementById('log-panel');
                if (panel) {{
                    const entry = document.createElement('div');
                    entry.style.display = 'contents';
                    entry.innerHTML = `{log_html.replace('`', '\\`').replace('\\n', '<br>')}`;
                    Array.from(entry.children).reverse().forEach(c => panel.prepend(c));
                    while (panel.childElementCount > ({LOG_DISPLAY_LINES} * 3)) {{
                        for(let i=0; i<3; i++) panel.removeChild(panel.lastChild);
                    }}
                }}"""
                self._execute_js(js_code)
                self.last_log_id = log['id']
        except Exception:
            # 啟動初期資料庫可能正在被寫入，忽略鎖定錯誤
            pass

    def run(self):
        while not self.is_ui_setup:
            time.sleep(0.1) # 等待 UI 初始化

        while not self.stop_event.is_set():
            self._update_status_bar()
            self._update_log_panel()
            time.sleep(0.1)

# --- Colab 啟動器 ---
def create_public_portal(port):
    """在 Colab 中建立一個公開的服務入口。"""
    try:
        with colab_output.redirect_to_element('#portal-container'):
            display(Javascript("document.getElementById('portal-container').innerHTML = '';"))
            colab_output.serve_kernel_port_as_iframe(port, path='/', height=500)
        print(f"✅ [成功] Colab 服務入口已發布。")
    except Exception as e:
        print(f"🟠 [警告] 建立 Colab 服務入口失敗: {e}")

def start_core_engine_in_background():
    """在背景線程中啟動核心引擎。"""
    def run_core():
        try:
            import core_run
            core_run.main()
        except (ImportError, ModuleNotFoundError):
            print("🔴 [嚴重錯誤] 找不到 `core_run` 模組。")
            print("🔴 請確認您已在 Poetry 環境中，並且 `core_run.py` 位於專案根目錄。")
            print("🔴 儀表板將無法接收到任何日誌。")
            STOP_EVENT.set() # 停止 UI 刷新
        except Exception as e:
            print(f"🔴 [嚴重錯誤] 核心引擎 `core_run` 執行時發生未預期錯誤: {e}")
            import traceback
            traceback.print_exc()
            STOP_EVENT.set() # 停止 UI 刷新

    print("🔵 [資訊] 正在背景線程中啟動核心引擎...")
    core_thread = threading.Thread(target=run_core, name="CoreEngineThread")
    core_thread.daemon = True
    core_thread.start()
    return core_thread


# --- 主流程 ---
def main():
    """Colab 儀表板的主執行流程。"""

    # --- 階段一：初始化儀表板 UI ---
    print("🔵 [資訊] 正在初始化 Colab 戰情儀表板...")
    display_manager = DisplayManager(DB_PATH, STOP_EVENT)
    display_manager.setup_ui()
    display_manager.start()

    # --- 階段二：在背景啟動核心引擎 ---
    core_thread = start_core_engine_in_background()

    # --- 階段三：等待核心引擎日誌 ---
    print("🔵 [資訊] 等待核心引擎初始化日誌...")
    start_time = time.time()
    while not DB_PATH.exists() and time.time() - start_time < 30:
        time.sleep(0.5)

    if not DB_PATH.exists():
        print("🔴 [錯誤] 等待核心引擎日誌超時。儀表板可能無法正常工作。")
    else:
        print("✅ [成功] 已偵測到核心引擎日誌。儀表板已連線。")

    # --- 階段四：發布服務入口 ---
    # 從 core_run 導入 PORT，如果失敗則使用預設值
    try:
        from core_run import FASTAPI_PORT
    except (ImportError, NameError):
        FASTAPI_PORT = 8000
        print(f"🟠 [警告] 無法從 `core_run` 獲取埠號，將使用預設值: {FASTAPI_PORT}")

    print(f"🔵 [資訊] 準備為埠號 {FASTAPI_PORT} 建立 Colab 服務入口...")
    create_public_portal(FASTAPI_PORT)

    print("✅ [成功] Colab 儀表板已啟動。核心服務正在背景運行。")
    print("🔵 要停止所有服務，請點擊此儲存格的「中斷執行」(■) 按鈕。")

    try:
        # 保持主線程活躍以接收中斷信號
        while core_thread.is_alive():
            core_thread.join(timeout=1.0)

    except (KeyboardInterrupt, SystemExit):
        print("\n🔵 [資訊] 偵測到使用者手動中斷請求...")
    finally:
        STOP_EVENT.set()
        if display_manager.is_alive():
            display_manager.join(timeout=2)
        print("--- Colab 儀表板已關閉 ---")


if __name__ == "__main__":
    print("🔵 [資訊] 此為 Colab 儀表板啟動器。")
    print("🔵 [資訊] 請在 Colab 儲存格中，使用 `%run colab_run.py` 或導入後執行 `main()` 來啟動。")
    # 直接執行時提供一個模擬的啟動流程
    main()
