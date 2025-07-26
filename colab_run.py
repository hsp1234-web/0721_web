# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   核心檔案：colab_run.py (v2.0 升級版)                             ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       專案在 Colab 環境中的「啟動協調器」。它負責以正確的順序，      ║
# ║       初始化並啟動所有核心模組。                                     ║
# ║                                                                      ║
# ║   設計哲學：                                                         ║
# ║       自身邏輯極度簡化。它不再處理任何畫面顯示或日誌監聽的複雜      ║
# ║       邏輯。其唯一職責是：                                           ║
# ║       1. 建立「視覺指揮官」(PresentationManager)。                  ║
# ║       2. 建立其他模組，並將指揮官的「遙控器」交給它們。            ║
# ║       3. 啟動所有服務，然後進入待命狀態，將控制權完全交出。        ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

import time
import sys
from pathlib import Path

# 確保專案根目錄在系統路徑中
# 這段程式碼假設 colab_run.py 位於專案根目錄
# 如果不是，您可能需要調整路徑
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.presentation_manager import PresentationManager
from core.monitor import HardwareMonitor
from logger.main import Logger

def main_execution_logic(logger, pm):
    """
    模擬專案的主要業務邏輯。
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


def run_phoenix_heart():
    """
    專案啟動主函數。
    """
    pm = None
    monitor = None
    try:
        # --- 1. 初始化視覺指揮官 ---
        # 這是模擬的頂部 HTML 按鈕，您可以從其他地方載入
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
        pm = PresentationManager(log_lines=20)
        pm.setup_layout(button_html)

        # --- 2. 初始化其他模組，並將指揮官實例傳遞給它們 ---
        logger = Logger(presentation_manager=pm)
        monitor = HardwareMonitor(presentation_manager=pm, interval=1.0)

        # --- 3. 啟動所有服務 ---
        logger.info("正在啟動所有核心服務...")
        monitor.start()
        logger.info("硬體監控情報員已派出。")
        logger.success("所有服務已成功啟動，指揮中心上線！")

        # --- 4. 執行主要業務邏輯 ---
        main_execution_logic(logger, pm)

        # --- 5. 保持待命 (如果需要) ---
        # 在實際應用中，這裡可能是啟動 FastAPI 伺服器並等待
        # 為了演示，我們讓它在任務結束後繼續顯示狀態
        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        # 這裡的捕獲是為了確保即使在啟動階段被中斷，也能優雅關閉
        if pm:
            logger.warning("系統在啟動過程中被手動中斷！")
            pm.update_task_status("核心狀態：系統啟動被中斷")

    finally:
        # --- 6. 優雅關閉 ---
        if monitor:
            monitor.stop()
        if pm:
            pm.stop()
        print("--- 鳳凰之心指揮中心程序已結束 ---")


if __name__ == '__main__':
    # 這是 Colab 儲存格最終要呼叫的函數
    run_phoenix_heart()

