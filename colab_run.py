# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   🚀 colab_run.py (v5.0 分層渲染最終版)                              ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       這是鳳凰之心指揮中心的最終版「一體化核心」。它回歸並正確      ║
# ║       實作了最穩定、無閃爍的「分層式終端渲染」架構，同時滿足您      ║
# ║       對版面佈局（標題在上，按鈕在下）的最終要求。                   ║
# ║                                                                      ║
# ║   v5.0 更新：                                                        ║
# ║       - 終極架構回歸：全面採用「分層式終端渲染」，根除所有閃爍問題。  ║
# ║       - 嚴格通訊紀律：修復所有日誌系統的衝突，確保畫面純淨。         ║
# ║       - 精確版面控制：透過終端控制碼，實現標題、日誌、狀態、按鈕      ║
# ║         四個區域的獨立與穩定。                                       ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

# --- Part 1: 匯入所有必要的函式庫 ---
import sys
import threading
import time
import collections
import logging
import shutil
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
    """
    視覺指揮官 (分層渲染版)：精確控制終端畫面，實現無閃爍更新。
    """
    def __init__(self, log_lines=15, status_lines=2):
        # --- ANSI 終端控制碼 ---
        self.CURSOR_UP = '\033[A'
        self.CLEAR_LINE = '\033[K'
        self.SAVE_CURSOR = '\033[s'
        self.RESTORE_CURSOR = '\033[u'
        
        # --- 組態設定 ---
        self.log_lines_count = log_lines
        self.status_lines_count = status_lines
        self.total_dynamic_lines = log_lines + status_lines
        
        self.log_buffer = collections.deque(maxlen=log_lines)
        self.status_buffer = collections.deque(maxlen=status_lines)
        
        self.is_running = False
        self.lock = threading.Lock() # 確保多執行緒安全

    def _write_flush(self, text):
        sys.stdout.write(text)
        sys.stdout.flush()

    def setup_layout(self, top_html_content, bottom_html_content):
        """建立靜態佈局：頂部標題 -> 動態區 -> 底部按鈕"""
        with self.lock:
            if self.is_running: return
            
            # 1. 頂層 (靜態)：顯示標題
            display(HTML(top_html_content))
            
            # 2. 中層 (動態)：為日誌和狀態區預留足夠的空白行
            self._write_flush('\n' * (self.total_dynamic_lines + 1))
            
            # 3. 底層 (靜態)：顯示按鈕
            display(HTML(bottom_html_content))
            
            # 4. 設定「動態區」的繪製起點
            #    向上移動 (動態區行數 + 按鈕的間隔1行)
            move_up_cmd = f'\033[{self.total_dynamic_lines + 2}A'
            self._write_flush(move_up_cmd)
            # 儲存這個位置，作為我們未來所有更新的「原點」
            self._write_flush(self.SAVE_CURSOR)
            
            self.is_running = True
            self._redraw_dynamic_area() # 初始繪製

    def _redraw_dynamic_area(self):
        """重繪整個動態區域（日誌 + 狀態）"""
        self._write_flush(self.RESTORE_CURSOR) # 回到原點
        
        # 繪製日誌
        for i in range(self.log_lines_count):
            line = self.log_buffer[i] if i < len(self.log_buffer) else ""
            self._write_flush(f'{self.CLEAR_LINE}{line}\n')
            
        # 繪製狀態
        for i in range(self.status_lines_count):
            line = self.status_buffer[i] if i < len(self.status_buffer) else ""
            self._write_flush(f'{self.CLEAR_LINE}{line}\n')

    def add_log(self, message):
        if not self.is_running: return
        with self.lock:
            self.log_buffer.append(message)
            self._redraw_dynamic_area()

    def update_status(self, status_list):
        if not self.is_running: return
        with self.lock:
            self.status_buffer.clear()
            self.status_buffer.extend(status_list)
            self._redraw_dynamic_area()

    def stop(self):
        if not self.is_running: return
        with self.lock:
            self.is_running = False
            # 將游標移動到所有內容的最下方，以避免破壞畫面
            self._write_flush(self.RESTORE_CURSOR)
            move_down_cmd = f'\033[{self.total_dynamic_lines + 1}B'
            self._write_flush(f"{move_down_cmd}\n")
        print("--- [PresentationManager] 視覺指揮官已停止運作 ---")


class Logger:
    """戰地記錄官 (通訊紀律修正版)"""
    COLORS = {"INFO": "\033[97m", "BATTLE": "\033[96m", "SUCCESS": "\033[92m", "WARNING": "\033[93m", "ERROR": "\033[91m", "CRITICAL": "\033[91;1m", "RESET": "\033[0m"}
    CUSTOM_LEVELS = {"BATTLE": 25, "SUCCESS": 26}

    def __init__(self, presentation_manager, timezone="Asia/Taipei"):
        self.pm = presentation_manager
        self.timezone = pytz.timezone(timezone)
        
        # 設定底層日誌系統
        for level_name, level_num in self.CUSTOM_LEVELS.items():
            logging.addLevelName(level_num, level_name)
        
        self.logger = logging.getLogger("PhoenixHeartLogger")
        self.logger.setLevel(logging.INFO)
        
        # --- 關鍵的「禁言令」 ---
        # 阻止日誌訊息被傳播到預設的、會產生混亂輸出的 handler
        self.logger.propagate = False

    def setup_file_handler(self, log_file_path):
        """設定檔案記錄器"""
        if not any(isinstance(h, logging.FileHandler) for h in self.logger.handlers):
            file_handler = TimedRotatingFileHandler(log_file_path, when="midnight", interval=1, backupCount=7, encoding='utf-8')
            file_handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s", datefmt='%Y-%m-%d %H:%M:%S'))
            self.logger.addHandler(file_handler)

    def _log(self, level, message, *args, **kwargs):
        level_upper = level.upper()
        # 記錄到檔案
        if level_upper in self.CUSTOM_LEVELS:
            self.logger.log(self.CUSTOM_LEVELS[level_upper], message, *args, **kwargs)
        else:
            getattr(self.logger, level.lower())(message, *args, **kwargs)
        
        # 傳送給視覺指揮官
        timestamp = datetime.now(self.timezone).strftime('%H:%M:%S.%f')[:-3]
        color = self.COLORS.get(level_upper, self.COLORS["INFO"])
        display_message = f"[{timestamp}] {color}[{level_upper:<7}]{self.COLORS['RESET']} {message}"
        self.pm.add_log(display_message)

    def info(self, m, *a, **kw): self._log("info", m, *a, **kw)
    def battle(self, m, *a, **kw): self._log("battle", m, *a, **kw)
    def success(self, m, *a, **kw): self._log("success", m, *a, **kw)
    def warning(self, m, *a, **kw): self._log("warning", m, *a, **kw)
    def error(self, m, *a, **kw): self._log("error", m, *a, **kw)
    def critical(self, m, *a, **kw): self._log("critical", m, *a, **kw)


class StatusUpdater:
    """狀態更新器：在背景執行緒中收集並更新狀態"""
    def __init__(self, presentation_manager, stats, interval=1.0):
        self.pm = presentation_manager
        self.stats = stats
        self.interval = interval
        self.is_running = False
        self._thread = None
        self.STATUS_LIGHTS = {"正常": "🟢", "警告": "🟡", "錯誤": "🔴", "完成": "✅", "待機": "⚪️"}

    def _update_loop(self):
        self.is_running = True
        while self.is_running:
            try:
                # 收集所有狀態訊息
                light = self.STATUS_LIGHTS.get(self.stats.get("light", "待機"), "⚪️")
                status_line_1 = f"{light} 核心狀態：{self.stats.get('task_status', '待命中...')}"
                
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                ts = datetime.now().strftime('%H:%M:%S')
                status_line_2 = f"💻 硬體監控：[{ts}] CPU: {cpu:5.1f}% | RAM: {ram:5.1f}%"
                
                # 一次性更新所有狀態行
                self.pm.update_status([status_line_1, status_line_2])
                
                time.sleep(self.interval)
            except Exception:
                # 確保更新迴圈不會因意外錯誤而崩潰
                pass

    def start(self):
        if not self.is_running:
            self._thread = threading.Thread(target=self._update_loop, daemon=True)
            self._thread.start()

    def stop(self):
        self.is_running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=self.interval * 2)


# █▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀█
# █   Part 3: 主要業務邏輯與啟動協調器                                  █
# █▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄█

def main_execution_logic(logger, stats):
    """專案的主要業務邏輯"""
    try:
        stats["light"] = "正常"
        stats["task_status"] = "正在執行主要任務"
        logger.info("主業務邏輯開始執行...")
        
        for i in range(1, 11):
            logger.battle(f"正在處理第 {i}/10 階段的戰鬥任務...")
            stats["task_status"] = f"任務進度 {i}/10"
            time.sleep(0.5)
            if i == 7:
                stats["light"] = "警告"
                logger.warning("偵測到 API 回應延遲，已自動重試...")
            if i % 5 == 0:
                logger.success(f"第 {i} 階段作戰節點順利完成！")
        
        stats["light"] = "完成"
        stats["task_status"] = "所有主要業務邏輯已成功執行完畢！"
        logger.success(stats["task_status"])
        
        time.sleep(2)
        stats["light"] = "待機"
        stats["task_status"] = "任務完成，系統待命中"

    except KeyboardInterrupt:
        stats["light"] = "警告"
        stats["task_status"] = "使用者手動中斷"
        logger.warning("偵測到手動中斷信號！")
    except Exception as e:
        stats["light"] = "錯誤"
        stats["task_status"] = f"發生致命錯誤！"
        logger.error(f"主業務邏輯發生未預期錯誤: {e}")

def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path):
    """專案啟動主函數，由 Colab 儲存格呼叫"""
    pm, status_updater, logger = None, None, None
    stats = {"task_status": "準備中...", "light": "正常"}

    try:
        # --- 1. 準備靜態 HTML 內容 ---
        top_html = """<div style="border-bottom: 2px solid #00BCD4; padding-bottom: 5px; margin-bottom: 10px;"><h2 style="text-align:center; color:#00BCD4; font-family:'Orbitron', sans-serif; margin:0;">🚀 鳳凰之心指揮中心 v5.0 🚀</h2></div>"""
        bottom_html = """<div style="border-top: 2px solid #00BCD4; padding-top: 10px; margin-top: 10px;"><p style="text-align:center; margin:0;"><a href="YOUR_FASTAPI_URL_PLACEHOLDER" target="_blank" style="background-color:#00BCD4; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; font-weight:bold;">開啟網頁操作介面</a></p></div>"""

        # --- 2. 初始化核心模組 ---
        pm = PresentationManager(log_lines=log_lines, status_lines=2)
        logger = Logger(presentation_manager=pm, timezone=timezone)
        status_updater = StatusUpdater(presentation_manager=pm, stats=stats)
        
        # --- 3. 建立佈局並啟動服務 ---
        pm.setup_layout(top_html, bottom_html)
        logger.info("視覺指揮官已啟動。")
        
        log_dir = project_path / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"日誌-{datetime.now(pytz.timezone(timezone)).strftime('%Y-%m-%d')}.md"
        logger.setup_file_handler(log_file)
        logger.info(f"檔案日誌系統已設定，將記錄至 {log_file}")
        
        status_updater.start()
        logger.info("狀態更新情報員已派出。")
        logger.success("所有服務已成功啟動，指揮中心上線！")

        # --- 4. 執行主要業務邏輯 ---
        main_execution_logic(logger, stats)

        # --- 5. 保持待命 ---
        while True: time.sleep(1)

    except KeyboardInterrupt:
        if logger: logger.warning("系統在運行中被手動中斷！")
    finally:
        # --- 6. 優雅關閉 ---
        if status_updater: status_updater.stop()
        if pm: pm.stop()

        # --- 7. 執行日誌歸檔 ---
        if 'log_file' in locals() and archive_folder_name and archive_folder_name.strip():
            print(f"\n--- 執行日誌歸檔 (台北時區) ---")
            try:
                source_log_path = log_file
                archive_folder_path = base_path / archive_folder_name.strip()
                if source_log_path.exists():
                    archive_folder_path.mkdir(exist_ok=True)
                    ts_str = datetime.now(pytz.timezone(timezone)).strftime("%Y%m%d_%H%M%S")
                    dest_path = archive_folder_path / f"日誌_{ts_str}.md"
                    shutil.copy2(source_log_path, dest_path)
                    print(f"✅ 日誌已成功歸檔至: {dest_path}")
                else:
                    print(f"⚠️  警告：找不到來源日誌檔 {source_log_path}。")
            except Exception as e: print(f"💥 歸檔期間發生錯誤: {e}")
        
        print("--- 鳳凰之心指揮中心程序已結束 ---")
