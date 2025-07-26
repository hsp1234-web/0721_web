# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║   核心檔案：colab_run.py (v2.1 台北時區強化版)                     ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   功能：                                                             ║
# ║       專案在 Colab 環境中的「啟動協調器」。它負責以正確的順序，      ║
# ║       初始化並啟動所有核心模組。                                     ║
# ║                                                                      ║
# ║   v2.1 更新：                                                        ║
# ║       在程式結束時的「日誌歸檔」邏輯中，導入 `pytz` 與 `datetime`   ║
# ║       函式庫，確保歸檔檔案的命名和尋找，都基於 `Asia/Taipei` 時區。 ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

import time
import sys
import shutil
from pathlib import Path
import pytz
from datetime import datetime

# 假設其他 import 語句已存在
from core.presentation_manager import PresentationManager
from core.monitor import HardwareMonitor
from logger.main import Logger

# --- 參數設定 (可移至 Colab form) ---
LOG_ARCHIVE_FOLDER_NAME = "作戰日誌歸檔"
PROJECT_FOLDER_NAME = "WEB"
TIMEZONE = "Asia/Taipei"

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


def run_phoenix_heart():
    """
    專案啟動主函數。
    """
    pm = None
    monitor = None
    logger = None
    base_path = Path("/content")
    project_path = base_path / PROJECT_FOLDER_NAME

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
        pm = PresentationManager(log_lines=20)
        pm.setup_layout(button_html)

        # --- 2. 初始化其他模組 ---
        logger = Logger(presentation_manager=pm, timezone=TIMEZONE)
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
            logger.warning("系統在啟動過程中被手動中斷！")
        if pm:
            pm.update_task_status("核心狀態：系統啟動被中斷")

    finally:
        # --- 5. 優雅關閉 ---
        if monitor:
            monitor.stop()

        # --- 6. 執行日誌歸檔 (台北時區強化版) ---
        if LOG_ARCHIVE_FOLDER_NAME and LOG_ARCHIVE_FOLDER_NAME.strip():
            print("\n--- 執行日誌歸檔 (台北時區) ---")
            try:
                # 建立時區物件
                tz = pytz.timezone(TIMEZONE)
                now_in_tz = datetime.now(tz)

                # 使用台北時區的「今天」日期來尋找來源日誌檔
                today_str = now_in_tz.strftime('%Y-%m-%d')
                source_log_path = project_path / "logs" / f"日誌-{today_str}.md"
                
                archive_folder_path = base_path / LOG_ARCHIVE_FOLDER_NAME.strip()

                if source_log_path.exists():
                    archive_folder_path.mkdir(exist_ok=True)
                    # 使用台北時區的「現在」時間來命名歸檔檔案
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


# if __name__ == '__main__':
#     # 在 Colab 中，我們會直接呼叫 run_phoenix_heart()
#     # 而不是透過 if __name__ == '__main__'
#     pass
