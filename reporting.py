# -*- coding: utf-8 -*-
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import pytz
import json

# --- 常數設定 ---
# 使用相對路徑，假設此腳本在專案根目錄下被 run.py 呼叫
DB_FILE = Path("state.db")
REPORTS_BASE_DIR = Path("報告")

def get_taipei_time() -> (datetime, str):
    """獲取當前的台北時間，並回傳日期時間物件和 ISO 格式的字串"""
    taipei_tz = pytz.timezone("Asia/Taipei")
    now_utc = datetime.utcnow().replace(tzinfo=pytz.utc)
    now_taipei = now_utc.astimezone(taipei_tz)
    # 格式化字串，移除毫秒並用連字號取代冒號，以利於作為資料夾名稱
    iso_string = now_taipei.isoformat(timespec='seconds').replace(':', '-')
    return now_taipei, iso_string

def create_final_reports():
    """
    在程式結束時，連線到資料庫，讀取所有數據，
    並產生三份詳細的 Markdown 格式報告。
    報告會儲存在一個以台北時間戳記命名的資料夾中。
    """
    print("--- 報告生成程序啟動 ---")

    # --- 1. 檢查資料庫是否存在 ---
    if not DB_FILE.exists():
        print(f"❌ 錯誤：找不到資料庫檔案 {DB_FILE}。無法生成報告。")
        return

    # --- 2. 設定報告儲存路徑 ---
    now_taipei, time_str = get_taipei_time()
    report_dir = REPORTS_BASE_DIR / time_str
    try:
        report_dir.mkdir(parents=True, exist_ok=True)
        print(f"📂 報告將儲存於: {report_dir}")
    except OSError as e:
        print(f"❌ 錯誤：無法建立報告資料夾 {report_dir}。錯誤訊息: {e}")
        return

    # --- 3. 連線並讀取資料 ---
    try:
        conn = sqlite3.connect(f"file:{DB_FILE}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # 讀取最後的狀態
        final_status = cursor.execute('SELECT * FROM status_table WHERE id = 1').fetchone()
        # 讀取所有日誌
        all_logs = cursor.execute('SELECT * FROM log_table ORDER BY id ASC').fetchall()

        conn.close()
        print(f"✅ 成功從資料庫讀取 {len(all_logs)} 條日誌和最後狀態。")

    except sqlite3.OperationalError as e:
        print(f"❌ 錯誤：無法讀取資料庫 {DB_FILE}。錯誤訊息: {e}")
        # 即使無法讀取，也產生一個錯誤報告
        error_report_path = report_dir / "ERROR_REPORT.md"
        with open(error_report_path, 'w', encoding='utf-8') as f:
            f.write(f"# 報告生成失敗\n\n")
            f.write(f"在 `{now_taipei.strftime('%Y-%m-%d %H:%M:%S')}` (台北時間) 嘗試生成報告時發生錯誤。\n\n")
            f.write(f"**錯誤詳情:**\n")
            f.write(f"```\n")
            f.write(f"無法讀取資料庫檔案: {DB_FILE}\n")
            f.write(f"SQLite 錯誤: {e}\n")
            f.write(f"```\n")
        return

    # --- 4. 生成報告 ---
    # 報告 A: 詳細日誌
    try:
        with open(report_dir / "詳細日誌.md", 'w', encoding='utf-8') as f:
            f.write(f"# 詳細日誌報告\n\n")
            f.write(f"- **生成時間:** `{now_taipei.strftime('%Y-%m-%d %H:%M:%S %Z')}`\n")
            f.write(f"- **總日誌數:** `{len(all_logs)}`\n\n")
            f.write("| 時間戳記 | 等級 | 訊息 |\n")
            f.write("|---|---|---|\n")
            for log in all_logs:
                # 確保訊息中的換行符和特殊字元不會破壞 Markdown 表格
                message = str(log['message']).replace('\n', '<br>')
                f.write(f"| `{log['timestamp']}` | {log['level']} | {message} |\n")
        print("📄 已生成「詳細日誌.md」")

    except Exception as e:
        print(f"❌ 錯誤：生成「詳細日誌.md」失敗: {e}")


    # 報告 B: 詳細效能
    try:
        with open(report_dir / "詳細效能.md", 'w', encoding='utf-8') as f:
            f.write(f"# 詳細效能報告\n\n")
            f.write(f"- **生成時間:** `{now_taipei.strftime('%Y-%m-%d %H:%M:%S %Z')}`\n\n")
            if final_status:
                f.write("## 系統最終狀態\n\n")
                f.write(f"- **CPU 使用率:** `{final_status['cpu_usage']:.2f}%`\n")
                f.write(f"- **RAM 使用率:** `{final_status['ram_usage']:.2f}%`\n\n")
                f.write("## 已安裝的 Python 套件\n\n")
                f.write("| 套件名稱 | 版本 |\n")
                f.write("|---|---|\n")
                try:
                    packages = json.loads(final_status['packages'] or '[]')
                    for pkg in packages:
                        f.write(f"| {pkg.get('name', 'N/A')} | {pkg.get('version', 'N/A')} |\n")
                except (json.JSONDecodeError, TypeError) as e:
                    f.write(f"| 解析套件列表失敗: {e} | N/A |\n")
            else:
                f.write("無法讀取最終系統狀態。\n")
        print("📄 已生成「詳細效能.md」")

    except Exception as e:
        print(f"❌ 錯誤：生成「詳細效能.md」失敗: {e}")

    # 報告 C: 綜合摘要
    try:
        with open(report_dir / "綜合摘要.md", 'w', encoding='utf-8') as f:
            f.write(f"# 綜合摘要報告\n\n")
            f.write(f"- **報告時間:** `{now_taipei.strftime('%Y-%m-%d %H:%M:%S %Z')}`\n\n")

            if final_status:
                start_time = datetime.fromisoformat(all_logs[0]['timestamp']) if all_logs else None
                end_time = datetime.fromisoformat(all_logs[-1]['timestamp']) if all_logs else None
                duration = (end_time - start_time) if start_time and end_time else "N/A"

                f.write("## 執行摘要\n\n")
                f.write(f"- **最終階段:** `{final_status['current_stage']}`\n")
                f.write(f"- **總執行時間:** `{str(duration).split('.')[0]}` (時:分:秒)\n")
                f.write(f"- **最終操作 URL:** {final_status['action_url'] or '未產生'}\n\n")

                f.write("## 微服務狀態\n\n")
                f.write("| 服務名稱 | 最終狀態 |\n")
                f.write("|---|---|\n")
                try:
                    apps_status = json.loads(final_status['apps_status'] or '{}')
                    for app, status in apps_status.items():
                        f.write(f"| {app} | {status} |\n")
                except (json.JSONDecodeError, TypeError) as e:
                     f.write(f"| 解析服務狀態失敗: {e} | N/A |\n")

                f.write("\n## 關鍵日誌摘要\n\n")
                errors = [log for log in all_logs if log['level'] in ('ERROR', 'CRITICAL')]
                warnings = [log for log in all_logs if log['level'] == 'WARNING']
                f.write(f"- **錯誤與嚴重錯誤:** `{len(errors)}` 則\n")
                f.write(f"- **警告:** `{len(warnings)}` 則\n\n")

                if errors:
                    f.write("### 最後 5 則錯誤/嚴重錯誤:\n\n")
                    for error in errors[-5:]:
                        f.write(f"- `{error['timestamp']}`: {error['message']}\n")
            else:
                f.write("無法讀取最終系統狀態，無法生成摘要。\n")
        print("📄 已生成「綜合摘要.md」")

    except Exception as e:
        print(f"❌ 錯誤：生成「綜合摘要.md」失敗: {e}")

    print("--- 報告生成完畢 ---")


if __name__ == '__main__':
    # 這是一個方便直接執行的測試入口
    print("執行 reporting.py 進行單獨測試...")
    # 為了測試，我們需要確保資料庫檔案存在，
    # 在真實情境中，run.py 會建立它。
    if not DB_FILE.exists():
        print(f"警告: 測試用的資料庫檔案 {DB_FILE} 不存在。")
    else:
        create_final_reports()
