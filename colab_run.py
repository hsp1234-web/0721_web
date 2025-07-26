# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   核心檔案：colab_run.py (v2.2 參數接收版)                         ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       專案在 Colab 環境中的「啟動協調器」。它負責以正確的順序，      ║
# ║       初始化並啟動所有核心模組。                                     ║
# ║                                                                      ║
# ║   v2.2 更新：                                                        ║
# ║       修正了 `run_phoenix_heart` 函數的定義，使其能夠正確接收並     ║
# ║       處理從 Colab 儲存格傳遞過來的參數 (如 log_lines, timezone     ║
# ║       等)，解決了 `TypeError` 的問題。                              ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

import time
import sys
import shutil
from pathlib import Path
import pytz
from datetime import datetime

# 確保專案根目錄在系統路徑中
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from core.presentation_manager import PresentationManager
from core.monitor import HardwareMonitor
from logger.main import Logger

def main_execution_logic(logger, pm):
    """
    模擬專案的主要業務邏輯。
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


# === 關鍵修正：更新函數定義以接收所有參數 ===
def run_phoenix_heart(log_lines, archive_folder_name, timezone, project_path, base_path):
    """
    專案啟動主函數，現在可以接收來自 Colab 的設定。
    """
    pm = None
    monitor = None
    logger = None

    try:
        # --- 1. 初始化視覺指揮官 ---
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

        # --- 2. 初始化其他模組 ---
        logger = Logger(presentation_manager=pm, timezone=timezone)
        monitor = HardwareMonitor(presentation_manager=pm, interval=1.0)

        # --- 3. 啟動所有服務 ---
        logger.info("正在啟動所有核心服務...")
        monitor.start()
        logger.info("硬體監控情報員已派出。")
        logger.success("所有服務已成功啟動，指揮中心上線！")

        # --- 4. 執行主要業務邏輯 ---
        main_execution_logic(logger, pm)

        while True:
            time.sleep(1)

    except KeyboardInterrupt:
        if logger:
            logger.warning("系統在運行中被手動中斷！")
        if pm:
            pm.update_task_status("核心狀態：系統已被中斷")

    finally:
        # --- 5. 優雅關閉 ---
        if monitor:
            monitor.stop()

        # --- 6. 執行日誌歸檔 ---
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

        if pm:
            pm.stop()
        print("--- 鳳凰之心指揮中心程序已結束 ---")
