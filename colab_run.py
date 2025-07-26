# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 colab_run.py (v3.2 語法修正最終版)                              ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       這是鳳凰之心指揮中心的「一體化核心」。它整合了所有必要的      ║
# ║       模組，提供完整的原生儀表板功能。                               ║
# ║                                                                      ║
# ║   v3.2 更新：                                                        ║
# ║       修正了 PresentationManager 中因 f-string 使用不當而導致的      ║
# ║       `SyntaxError`。將有問題的程式碼拆分為多行，確保語法正確性，   ║
# ║       這是啟動流程的最終修正。                                       ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- Part 1: 匯入所有必要的函式庫 ---
import sys
import threading
import time
import collections
import logging
import shutil
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from datetime import datetime

try:
    import psutil
    import pytz
    from IPython.display import display, HTML
except ImportError as e:
    print(f"💥 核心套件匯入失敗: {e}")
    print("請確保在 Colab 儲存格中已透過 requirements.txt 正確安裝 psutil 與 pytz。")
    sys.exit(1)


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 2: 核心類別定義 (視覺、日誌、監控)                           █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

class PresentationManager:
    """視覺指揮官"""
    def __init__(self, log_lines=20):
        self.CURSOR_UP, self.CLEAR_LINE, self.SAVE_CURSOR, self.RESTORE_CURSOR = '\033[A', '\033[K', '\033[s', '\033[u'
        self.log_lines_count = log_lines
        self.log_buffer = collections.deque(maxlen=log_lines)
        self.status_text, self.hardware_text = "核心狀態：初始化中...", "硬體監控：待命中..."
        self.is_running, self.lock = False, threading.Lock()

    def _write_flush(self, text):
        sys.stdout.write(text); sys.stdout.flush()

    def setup_layout(self, top_html_content):
        with self.lock:
            if self.is_running: return
            display(HTML(top_html_content))
            # === 關鍵語法修正：將有問題的 f-string 拆分為清晰的多行 ===
            # 1. 為日誌區域預留空白行
            self._write_flush('\n' * (self.log_lines_count + 1))
            # 2. 為狀態列預留一行
            self._write_flush('\n')
            # 3. 將游標向上移動並儲存位置
            move_and_save_cmd = f'\033[{self.log_lines_count + 1}A{self.SAVE_CURSOR}'
            self._write_flush(move_and_save_cmd)
            
            self.is_running = True
            self._redraw_all()

    def _redraw_logs(self):
        self._write_flush(self.RESTORE_CURSOR)
        for i in range(self.log_lines_count):
            line = self.log_buffer[i] if i < len(self.log_buffer) else ""
            self._write_flush(f'{self.CLEAR_LINE}{line}\n')

    def _redraw_status_line(self):
        move_down_cmd = f'\033[{self.log_lines_count + 1}B'
        self._write_flush(f"{self.RESTORE_CURSOR}{move_down_cmd}")
        self._write_flush(f'\r{self.CLEAR_LINE}{self.hardware_text} | {self.status_text}')
        self._write_flush(self.RESTORE_CURSOR)

    def _redraw_all(self): self._redraw_logs(); self._redraw_status_line()
    def add_log(self, message):
        if self.is_running:
            with self.lock: self.log_buffer.append(message); self._redraw_logs()
    def update_task_status(self, status):
        if self.is_running:
            with self.lock: self.status_text = status; self._redraw_status_line()
    def update_hardware_status(self, hardware_string):
        if self.is_running:
            with self.lock: self.hardware_text = hardware_string; self._redraw_status_line()

    def stop(self):
        if self.is_running:
            with self.lock:
                self.is_running = False
                move_down_cmd = f'\033[{self.log_lines_count + 2}B'
                self._write_flush(f"{self.RESTORE_CURSOR}{move_down_cmd}\n")
            print("--- [PresentationManager] 視覺指揮官已停止運作 ---")


class Logger:
    """戰地記錄官"""
    COLORS = {"INFO": "\033[97m", "BATTLE": "\033[96m", "SUCCESS": "\033[92m", "WARNING": "\033[93m", "ERROR": "\033[91m", "CRITICAL": "\033[91;1m", "RESET": "\033[0m"}
    CUSTOM_LEVELS = {"BATTLE": 25, "SUCCESS": 26}

    def __init__(self, presentation_manager, log_dir="logs", timezone="Asia/Taipei"):
        self.pm = presentation_manager
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.timezone = pytz.timezone(timezone)
        
        logging.addLevelName(self.CUSTOM_LEVELS["BATTLE"], "BATTLE")
        logging.addLevelName(self.CUSTOM_LEVELS["SUCCESS"], "SUCCESS")
        
        self.logger = logging.getLogger("PhoenixHeartLogger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            today_in_tz = datetime.now(self.timezone).strftime('%Y-%m-%d')
            log_file = self.log_dir / f"日誌-{today_in_tz}.md"
            file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S'))
            self.logger.addHandler(file_handler)

    def _log(self, level, message, *args, **kwargs):
        level_upper = level.upper()
        if level_upper in self.CUSTOM_LEVELS:
            self.logger.log(self.CUSTOM_LEVELS[level_upper], message, *args, **kwargs)
        else:
            getattr(self.logger, level.lower())(message, *args, **kwargs)
        
        timestamp = datetime.now(self.timezone).strftime('%H:%M:%S.%f')[:-3]
        color = self.COLORS.get(level_upper, self.COLORS["INFO"])
        display_message = f"[{timestamp}] {color}[{level_upper}]{self.COLORS['RESET']} {message}"
        self.pm.add_log(display_message)

    def info(self, m, *a, **kw): self._log("info", m, *a, **kw)
    def battle(self, m, *a, **kw): self._log("battle", m, *a, **kw)
    def success(self, m, *a, **kw): self._log("success", m, *a, **kw)
    def warning(self, m, *a, **kw): self._log("warning", m, *a, **kw)
    def error(self, m, *a, **kw): self._log("error", m, *a, **kw)
    def critical(self, m, *a, **kw): self._log("critical", m, *a, **kw)


class HardwareMonitor:
    """情報員"""
    def __init__(self, presentation_manager, interval=1.0):
        self.pm, self.interval, self.is_running, self._thread = presentation_manager, interval, False, None

    def _monitor(self):
        self.is_running = True
        while self.is_running:
            try:
                ts = datetime.now().strftime('%H:%M:%S')
                hw_str = f"[{ts}] CPU: {psutil.cpu_percent():5.1f}% | RAM: {psutil.virtual_memory().percent:5.1f}%"
                self.pm.update_hardware_status(hw_str)
                time.sleep(self.interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied): self.pm.update_hardware_status("硬體監控：程序結束"); break
            except Exception: self.pm.update_hardware_status("硬體監控：發生錯誤"); break

    def start(self):
        if not self.is_running: self._thread = threading.Thread(target=self._monitor, daemon=True); self._thread.start()
    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive(): self._thread.join(timeout=self.interval * 2)


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 3: 主要業務邏輯與啟動協調器                                  █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

def main_execution_logic(logger, pm):
    """專案的主要業務邏輯"""
    try:
        logger.info("主業務邏輯開始執行...")
        pm.update_task_status("核心狀態：正在執行主要任務")
        for i in range(1, 11):
            logger.battle(f"正在處理第 {i}/10 階段的戰鬥任務...")
            pm.update_task_status(f"核心狀態：任務進度 {i}/10")
            time.sleep(0.5)
            if i % 5 == 0: logger.success(f"第 {i} 階段作戰節點順利完成！")
        logger.success("所有主要業務邏輯已成功執行完畢！")
        pm.update_task_status("核心狀態：任務完成，系統待命中")
    except KeyboardInterrupt:
        logger.warning("偵測到手動中斷信號！")
        pm.update_task_status("核心狀態：使用者手動中斷")
    except Exception as e:
        logger.error(f"主業務邏輯發生未預期錯誤: {e}")
        pm.update_task_status(f"核心狀態：發生致命錯誤！")

def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path):
    """專案啟動主函數，由 Colab 儲存格呼叫"""
    pm, monitor, logger = None, None, None
    try:
        button_html = """<div style="border:2px solid #00BCD4;padding:10px;border-radius:8px;background-color:#1a1a1a;"><h2 style="text-align:center;color:#00BCD4;font-family:'Orbitron',sans-serif;">🚀 鳳凰之心指揮中心 🚀</h2><p style="text-align:center;"><a href="YOUR_FASTAPI_URL_PLACEHOLDER" target="_blank" style="background-color:#00BCD4;color:white;padding:10px 20px;text-decoration:none;border-radius:5px;font-weight:bold;">開啟網頁操作介面</a></p></div>"""
        pm = PresentationManager(log_lines=log_lines)
        pm.setup_layout(button_html)
        logger = Logger(presentation_manager=pm, timezone=timezone)
        monitor = HardwareMonitor(presentation_manager=pm, interval=1.0)
        logger.info("正在啟動所有核心服務...")
        monitor.start()
        logger.info("硬體監控情報員已派出。")
        logger.success("所有服務已成功啟動，指揮中心上線！")
        main_execution_logic(logger, pm)
        while True: time.sleep(1)
    except KeyboardInterrupt:
        if logger: logger.warning("系統在運行中被手動中斷！")
        if pm: pm.update_task_status("核心狀態：系統已被中斷")
    finally:
        if monitor: monitor.stop()
        if archive_folder_name and archive_folder_name.strip():
            print("\n--- 執行日誌歸檔 (台北時區) ---")
            try:
                tz, now_in_tz = pytz.timezone(timezone), datetime.now(pytz.timezone(timezone))
                today_str = now_in_tz.strftime('%Y-%m-%d')
                source_log_path = project_path / "logs" / f"日誌-{today_str}.md"
                archive_folder_path = base_path / archive_folder_name.strip()
                if source_log_path.exists():
                    archive_folder_path.mkdir(exist_ok=True)
                    ts_str = now_in_tz.strftime("%Y%m%d_%H%M%S")
                    dest_path = archive_folder_path / f"日誌_{ts_str}.md"
                    shutil.copy2(source_log_path, dest_path)
                    print(f"✅ 日誌已成功歸檔至: {dest_path}")
                else:
                    print(f"⚠️  警告：找不到來源日誌檔 {source_log_path}。")
            except Exception as e: print(f"💥 歸檔期間發生錯誤: {e}")
        if pm: pm.stop()
        print("--- 鳳凰之心指揮中心程序已結束 ---")
