# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 colab_run.py (v3.0 一體化最終版)                                ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       這是鳳凰之心指揮中心的「一體化核心」。它整合了所有必要的      ║
# ║       模組，包括視覺渲染、硬體監控、日誌記錄與主業務邏輯，以一個      ║
# ║       檔案的形式，提供完整的原生儀表板功能。                         ║
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       極致簡化維護流程。未來所有功能升級與錯誤修正，都只需要更新      ║
# ║       這一個檔案。徹底根除因多檔案版本不匹配而導致的所有錯誤。        ║
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

# 這些是 Colab 環境中預期會安裝的函式庫
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
    """
    視覺指揮官：管理 Colab 輸出畫面的類別，實現三層式渲染架構。
    """
    def __init__(self, log_lines=20):
        self.CURSOR_UP = '\033[A'
        self.CLEAR_LINE = '\033[K'
        self.SAVE_CURSOR = '\033[s'
        self.RESTORE_CURSOR = '\033[u'
        self.log_lines_count = log_lines
        self.log_buffer = collections.deque(maxlen=log_lines)
        self.status_text = "核心狀態：初始化中..."
        self.hardware_text = "硬體監控：待命中..."
        self.is_running = False
        self.lock = threading.Lock()

    def _write_flush(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def setup_layout(self, top_html_content):
        with self.lock:
            if self.is_running: return
            display(HTML(top_html_content))
            self._write_flush('\n' * (self.log_lines_count + 1))
            self._write_flush('\n')
            self._write_flush(f'\033[{self.log_lines_count + 1}A{self.SAVE_CURSOR}')
            self.is_running = True
            self._redraw_all()

    def _redraw_logs(self):
        self._write_flush(self.RESTORE_CURSOR)
        for i in range(self.log_lines_count):
            line = self.log_buffer[i] if i < len(self.log_buffer) else ""
            self._write_flush(f'{self.CLEAR_LINE}{line}\n')

    def _redraw_status_line(self):
        self._write_flush(self.RESTORE_CURSOR)
        self._write_flush(f'\033[{self.log_lines_count + 1}B')
        full_status = f"{self.hardware_text} | {self.status_text}"
        self._write_flush(f'\r{self.CLEAR_LINE}{full_status}')
        self._write_flush(self.RESTORE_CURSOR)

    def _redraw_all(self):
        self._redraw_logs()
        self._redraw_status_line()

    def add_log(self, message):
        if not self.is_running: return
        with self.lock:
            self.log_buffer.append(message)
            self._redraw_logs()

    def update_task_status(self, status):
        if not self.is_running: return
        with self.lock:
            self.status_text = status
            self._redraw_status_line()

    def update_hardware_status(self, hardware_string):
        if not self.is_running: return
        with self.lock:
            self.hardware_text = hardware_string
            self._redraw_status_line()

    def stop(self):
        if not self.is_running: return
        with self.lock:
            self.is_running = False
            self._write_flush(self.RESTORE_CURSOR)
            self._write_flush(f'\033[{self.log_lines_count + 2}B\n')
        print("--- [PresentationManager] 視覺指揮官已停止運作 ---")


class Logger:
    """
    戰地記錄官：處理所有日誌訊息，寫入檔案並抄送給視覺指揮官。
    """
    COLORS = {
        "INFO": "\033[97m", "BATTLE": "\033[96m", "SUCCESS": "\033[92m",
        "WARNING": "\033[93m", "ERROR": "\033[91m", "CRITICAL": "\033[91;1m",
        "RESET": "\033[0m"
    }

    def __init__(self, presentation_manager, log_dir="logs", timezone="Asia/Taipei"):
        self.pm = presentation_manager
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.timezone = pytz.timezone(timezone)
        logging.addLevelName(25, "BATTLE")
        logging.addLevelName(26, "SUCCESS")
        self.logger = logging.getLogger("PhoenixHeartLogger")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            today_in_tz = datetime.now(self.timezone).strftime('%Y-%m-%d')
            log_file = self.log_dir / f"日誌-{today_in_tz}.md"
            file_handler = TimedRotatingFileHandler(log_file, when="midnight", interval=1, backupCount=7, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S'))
            self.logger.addHandler(file_handler)

    def _log(self, level, message, *args, **kwargs):
        log_func = getattr(self.logger, level.lower())
        log_func(message, *args, **kwargs)
        timestamp = datetime.now(self.timezone).strftime('%H:%M:%S.%f')[:-3]
        level_upper = level.upper()
        color = self.COLORS.get(level_upper, self.COLORS["INFO"])
        reset_color = self.COLORS["RESET"]
        display_message = f"[{timestamp}] {color}[{level_upper}]{reset_color} {message}"
        self.pm.add_log(display_message)

    def info(self, m, *a, **kw): self._log("info", m, *a, **kw)
    def battle(self, m, *a, **kw): self._log("battle", m, *a, **kw)
    def success(self, m, *a, **kw): self._log("success", m, *a, **kw)
    def warning(self, m, *a, **kw): self._log("warning", m, *a, **kw)
    def error(self, m, *a, **kw): self._log("error", m, *a, **kw)
    def critical(self, m, *a, **kw): self._log("critical", m, *a, **kw)


class HardwareMonitor:
    """
    情報員：在背景偵測 CPU 與 RAM 使用率，並匯報給視覺指揮官。
    """
    def __init__(self, presentation_manager, interval=1.0):
        self.pm = presentation_manager
        self.interval = interval
        self.is_running = False
        self._thread = None

    def _monitor(self):
        self.is_running = True
        while self.is_running:
            try:
                cpu_percent = psutil.cpu_percent()
                ram_percent = psutil.virtual_memory().percent
                timestamp = datetime.now().strftime('%H:%M:%S')
                hardware_string = f"[{timestamp}] CPU: {cpu_percent:5.1f}% | RAM: {ram_percent:5.1f}%"
                self.pm.update_hardware_status(hardware_string)
                time.sleep(self.interval)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.pm.update_hardware_status("硬體監控：程序結束")
                break
            except Exception:
                self.pm.update_hardware_status("硬體監控：發生錯誤")
                break

    def start(self):
        if not self.is_running:
            self._thread = threading.Thread(target=self._monitor, daemon=True)
            self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval * 2)


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 3: 主要業務邏輯與啟動協調器                                  █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

def main_execution_logic(logger, pm):
    """
    專案的主要業務邏輯。
    所有進度更新和日誌記錄都透過傳入的 logger 和 pm 實例完成。
    """
    try:
        logger.info("主業務邏輯開始執行...")
        pm.update_task_status("核心狀態：正在執行主要任務")
        for i in range(1, 31):
            logger.battle(f"正在處理第 {i}/30 階段的戰鬥任務...")
            pm.update_task_status(f"核心狀態：任務進度 {i}/30")
            time.sleep(0.7)
            if i % 10 == 0:
                logger.success(f"第 {i} 階段作戰節點順利完成！")
        logger.success("所有主要業務邏輯已成功執行完畢！")
        pm.update_task_status("核心狀態：任務完成，系統待命中")
    except KeyboardInterrupt:
        logger.warning("偵測到手動中斷信號！")
        pm.update_task_status("核心狀態：使用者手動中斷")
    except Exception as e:
        logger.error(f"主業務邏輯發生未預期錯誤: {e}")
        pm.update_task_status(f"核心狀態：發生致命錯誤！")


def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path):
    """
    專案啟動主函數，由 Colab 儲存格呼叫。
    """
    pm = None
    monitor = None
    logger = None
    try:
        button_html = """
        <div style="border: 2px solid #00BCD4; padding: 10px; border-radius: 8px; background-color: #1a1a1a;">
            <h2 style="text-align:center; color:#00BCD4; font-family: 'Orbitron', sans-serif;">🚀 鳳凰之心指揮中心 🚀</h2>
            <p style="text-align:center;">
                <a href="YOUR_FASTAPI_URL_PLACEHOLDER" target="_blank" style="background-color: #00BCD4; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                    開啟網頁操作介面
                </a>
            </p>
        </div>
        """
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
                tz = pytz.timezone(timezone)
                now_in_tz = datetime.now(tz)
                today_str = now_in_tz.strftime('%Y-%m-%d')
                source_log_path = project_path / "logs" / f"日誌-{today_str}.md"
                archive_folder_path = base_path / archive_folder_name.strip()
                if source_log_path.exists():
                    archive_folder_path.mkdir(exist_ok=True)
                    timestamp_str = now_in_tz.strftime("%Y%m%d_%H%M%S")
                    destination_log_path = archive_folder_path / f"日誌_{timestamp_str}.md"
                    shutil.copy2(source_log_path, destination_log_path)
                    print(f"✅ 日誌已成功歸檔至: {destination_log_path}")
                else:
                    print(f"⚠️  警告：在台北時區 {today_str} 中，找不到來源日誌檔 {source_log_path}，無法歸檔。")
            except Exception as archive_e:
                print(f"💥 歸檔期間發生錯誤: {archive_e}")
        if pm: pm.stop()
        print("--- 鳳凰之心指揮中心程序已結束 ---")
