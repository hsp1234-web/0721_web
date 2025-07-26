# ╔══════════════════════════════════════════════════════════════════╗
# ║                🏃 run.py Colab 專用儀表板 v3.0 🏃                  ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                  ║
# ║  【功能重構】                                                    ║
# ║  1. **職責單一**: 此腳本現在只負責在 Colab 環境中啟動一個視覺化的 ║
# ║     儀表板，不再啟動任何網頁伺服器。                             ║
# ║  2. **核心整合**: 直接使用 `core` 模組中的 `PresentationManager`  ║
# ║     和 `HardwareMonitor` 來管理畫面顯示與硬體監控。              ║
# ║  3. **簡化依賴**: 移除了 `websockets`, `asyncio`, `subprocess` 等 ║
# ║     不再需要的依賴。                                             ║
# ║                                                                  ║
# ╚══════════════════════════════════════════════════════════════════╝

import time
import logging

# --- 核心模組匯入 ---
from core.presentation_manager import PresentationManager
from core.monitor import HardwareMonitor
from core.logging_config import setup_logger

def display_dashboard():
    """
    在 Colab 環境中顯示一個互動式儀表板。
    """
    # --- 1. 初始化 ---
    # 設定一個基本的日誌系統，輸出到控制台
    setup_logger()

    # 初始化視覺指揮官 (PresentationManager)
    pm = PresentationManager(log_lines=15)

    # 準備頂部靜態 HTML 內容
    top_html = """
    <div style="font-family: 'Courier New', monospace; background-color: #f0f0f0; padding: 15px; border-radius: 8px;">
        <h1 style="color: #333;">🚀 鳳凰之心 - Colab 監控儀表板 🚀</h1>
        <p style="color: #555;">這是一個純客戶端的監控畫面，用於展示系統狀態和日誌。</p>
    </div>
    """

    # --- 2. 啟動畫面與監控 ---
    pm.setup_layout(top_html)

    # 啟動硬體監控器，它會自動將資訊回報給 PresentationManager
    monitor = HardwareMonitor(presentation_manager=pm, interval=1.0)
    monitor.start()

    logging.info("儀表板啟動成功，視覺指揮官已接管畫面。")
    logging.info("硬體監控已啟動，每秒更新一次。")

    # --- 3. 模擬日誌流 ---
    # 這裡我們模擬一些來自不同系統模組的日誌訊息
    try:
        log_messages = [
            ("INFO", "正在初始化量化分析模組..."),
            ("INFO", "讀取歷史 K 線數據。"),
            ("BATTLE", "策略 '海龜湯' 開始回測..."),
            ("SUCCESS", "回測完成，夏普比率: 1.8。"),
            ("INFO", "正在初始化語音轉錄模組..."),
            ("BATTLE", "載入 Whisper 大型模型 (需要 5GB VRAM)..."),
            ("SUCCESS", "模型載入成功，系統準備就緒。"),
            ("WARNING", "偵測到磁碟空間低於 10%。"),
            ("INFO", "等待新的指令..."),
        ]

        for level, msg in log_messages:
            # 使用 logging 模組來記錄，而不是直接呼叫 pm.add_log
            # 這樣可以確保日誌同時被寫入檔案和顯示在儀表板上
            logging.log(logging.getLevelName(level), msg)
            time.sleep(0.8)

        # 讓儀表板持續顯示 30 秒
        logging.info("日誌模擬完成，儀表板將在 30 秒後關閉。")
        time.sleep(30)

    except KeyboardInterrupt:
        logging.warning("\n偵測到手動中斷，正在關閉儀表板...")
    finally:
        # --- 4. 清理資源 ---
        logging.info("正在停止硬體監控...")
        monitor.stop()

        logging.info("視覺指揮官正在釋放畫面控制權...")
        pm.stop()

        logging.info("儀表板已成功關閉。")

if __name__ == "__main__":
    # 在 Colab 或類似的 Jupyter 環境中，直接呼叫此函式即可啟動儀表板
    display_dashboard()
