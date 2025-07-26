# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   核心檔案：core/presentation_manager.py (v2.0 升級版)               ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       這是升級後的「視覺指揮官」，專案畫面的唯一控制核心。它以      ║
# ║       「分層式終端渲染」架構，實現了最穩定、流暢的儀表板體驗。      ║
# ║                                                                      ║
# ║       1. 頂層 (靜態)：顯示一次性的標題與操作按鈕。                 ║
# ║       2. 中層 (滾動)：優雅輪替顯示固定數量的最新日誌。             ║
# ║       3. 底層 (即時)：無閃爍原地更新硬體與任務狀態。               ║
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       將所有畫面控制的複雜性封裝於此，對外提供極簡介面。不依賴      ║
# ║       任何外部套件，僅使用 Python 內建功能與終端原生控制碼。        ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

import sys
import threading
import time
import collections
from IPython.display import display, HTML

class PresentationManager:
    """
    管理 Colab 輸出畫面的類別，實現三層式渲染架構。
    """

    def __init__(self, log_lines=20):
        # --- ANSI 終端控制碼 ---
        self.CURSOR_UP = '\033[A'
        self.CLEAR_LINE = '\033[K'
        self.SAVE_CURSOR = '\033[s'
        self.RESTORE_CURSOR = '\033[u'

        # --- 組態設定 ---
        self.log_lines_count = log_lines
        self.log_buffer = collections.deque(maxlen=log_lines)
        self.status_text = "核心狀態：初始化中..."
        self.hardware_text = "硬體監控：待命中..."
        self.is_running = False

        # --- 同步鎖，確保多執行緒安全 ---
        self.lock = threading.Lock()

    def _write_flush(self, text):
        """帶有 flush 的標準輸出，確保指令即時發送。"""
        sys.stdout.write(text)
        sys.stdout.flush()

    def setup_layout(self, top_html_content):
        """
        建立初始畫面佈局。此函數只在啟動時呼叫一次。
        """
        with self.lock:
            if self.is_running:
                return

            # 1. 頂層 (靜態)：顯示 HTML 內容 (標題和按鈕)
            display(HTML(top_html_content))

            # 2. 中層 (日誌)：為日誌區域預留空白行
            self._write_flush('\n' * (self.log_lines_count + 1))

            # 3. 底層 (狀態)：為狀態列預留一行
            self._write_flush('\n')

            # 4. 儲存游標位置：將日誌區的起始點儲存起來
            #    我們向上移動 (日誌行數 + 狀態列的1行)
            self._write_flush(f'\033[{self.log_lines_count + 1}A{self.SAVE_CURSOR}')
            self.is_running = True
            self._redraw_all()

    def _redraw_logs(self):
        """
        使用終端控制碼重繪日誌區域。
        """
        # 還原到日誌區的左上角
        self._write_flush(self.RESTORE_CURSOR)

        # 逐行繪製日誌
        for i in range(self.log_lines_count):
            line = self.log_buffer[i] if i < len(self.log_buffer) else ""
            self._write_flush(f'{self.CLEAR_LINE}{line}\n')

    def _redraw_status_line(self):
        """
        使用終端控制碼重繪最下方的狀態列。
        """
        # 1. 還原到日誌區左上角
        self._write_flush(self.RESTORE_CURSOR)
        # 2. 向下移動到狀態列
        self._write_flush(f'\033[{self.log_lines_count + 1}B')
        # 3. 組合完整的狀態文字
        full_status = f"{self.hardware_text} | {self.status_text}"
        # 4. 清除並寫入新的狀態文字 (使用 \r 回車來回到行首)
        self._write_flush(f'\r{self.CLEAR_LINE}{full_status}')
        # 5. 將游標移回日誌區，準備下次日誌更新
        self._write_flush(self.RESTORE_CURSOR)

    def _redraw_all(self):
        """重繪日誌區與狀態列。"""
        self._redraw_logs()
        self._redraw_status_line()

    def add_log(self, message):
        """
        【對外介面】向日誌緩衝區新增一條訊息，並觸發重繪。
        """
        if not self.is_running: return
        with self.lock:
            self.log_buffer.append(message)
            self._redraw_logs()

    def update_task_status(self, status):
        """
        【對外介面】更新任務狀態文字。
        """
        if not self.is_running: return
        with self.lock:
            self.status_text = status
            self._redraw_status_line()

    def update_hardware_status(self, hardware_string):
        """
        【對外介面】更新硬體狀態文字。
        """
        if not self.is_running: return
        with self.lock:
            self.hardware_text = hardware_string
            self._redraw_status_line()

    def stop(self):
        """
        停止所有更新並將游標移到最下方。
        """
        if not self.is_running: return
        with self.lock:
            self.is_running = False
            # 將游標移動到所有內容的最下方，以避免破壞畫面
            self._write_flush(self.RESTORE_CURSOR)
            self._write_flush(f'\033[{self.log_lines_count + 2}B\n')
        print("--- [PresentationManager] 視覺指揮官已停止運作 ---")

