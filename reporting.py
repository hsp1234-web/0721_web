# -*- coding: utf-8 -*-
import sqlite3
import json
import sys
import subprocess
from pathlib import Path
from datetime import datetime
try:
    import pytz
except ImportError:
    subprocess.run([sys.executable, '-m', 'pip', 'install', 'pytz'], check=True)
    import pytz

def create_final_reports():
    """
    在程式結束時，產生三份 Markdown 格式的報告。
    """
    # --- 設定時區和時間戳記 ---
    tz = pytz.timezone('Asia/Taipei')
    now = datetime.now(tz)
    timestamp_str = now.strftime("%Y-%m-%dT%H-%M-%S")

    # --- 建立報告目錄 ---
    report_dir = Path(f"/content/報告/{timestamp_str}")
    report_dir.mkdir(parents=True, exist_ok=True)

    # --- 連線到資料庫 ---
    db_file = Path("/content/WEB1/state.db")
    if not db_file.exists():
        print(f"❌ 找不到資料庫檔案: {db_file}")
        return

    conn = sqlite3.connect(db_file)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # --- 讀取數據 ---
    logs = cursor.execute("SELECT * FROM log_table ORDER BY timestamp ASC").fetchall()
    status = cursor.execute("SELECT * FROM status_table WHERE id = 1").fetchone()

    # --- 產生報告 ---
    _generate_log_report(report_dir, logs)
    _generate_performance_report(report_dir, status)
    _generate_summary_report(report_dir, logs, status)

    conn.close()
    print(f"✅ 報告已成功產生於: {report_dir}")

def _generate_log_report(report_dir, logs):
    """產生詳細日誌報告"""
    with open(report_dir / "詳細日誌.md", "w", encoding="utf-8") as f:
        f.write("# 詳細日誌報告\n\n")
        f.write("| 時間戳記 | 層級 | 訊息 |\n")
        f.write("|---|---|---|\n")
        for log in logs:
            f.write(f"| {log['timestamp']} | {log['level']} | {log['message']} |\n")

def _generate_performance_report(report_dir, status):
    """產生詳細效能報告"""
    with open(report_dir / "詳細效能.md", "w", encoding="utf-8") as f:
        f.write("# 詳細效能報告\n\n")
        if status:
            f.write("## 系統資源\n\n")
            f.write(f"- **CPU 使用率:** {status['cpu_usage']:.1f}%\n")
            f.write(f"- **RAM 使用率:** {status['ram_usage']:.1f}%\n\n")

            f.write("## 已安裝套件\n\n")
            f.write("| 套件名稱 | 版本 |\n")
            f.write("|---|---|\n")
            if status['packages']:
                packages = json.loads(status['packages'])
                for pkg in packages:
                    f.write(f"| {pkg['name']} | {pkg['version']} |\n")
        else:
            f.write("沒有可用的效能數據。\n")

def _generate_summary_report(report_dir, logs, status):
    """產生綜合摘要報告"""
    with open(report_dir / "綜合摘要.md", "w", encoding="utf-8") as f:
        f.write("# 綜合摘要報告\n\n")

        # --- 效能重點 ---
        f.write("## 效能重點\n\n")
        if status:
            f.write(f"- **最終 CPU 使用率:** {status['cpu_usage']:.1f}%\n")
            f.write(f"- **最終 RAM 使用率:** {status['ram_usage']:.1f}%\n")
            if status['packages']:
                f.write(f"- **已安裝套件數量:** {len(json.loads(status['packages']))}\n")
        else:
            f.write("沒有可用的效能數據。\n")

        # --- 日誌摘要 ---
        f.write("\n## 日誌摘要\n\n")
        if logs:
            total_logs = len(logs)
            error_logs = [log for log in logs if log['level'] in ('ERROR', 'CRITICAL')]
            warning_logs = [log for log in logs if log['level'] == 'WARNING']

            f.write(f"- **總日誌數量:** {total_logs}\n")
            f.write(f"- **錯誤日誌數量:** {len(error_logs)}\n")
            f.write(f"- **警告日誌數量:** {len(warning_logs)}\n\n")

            if error_logs:
                f.write("### 最後 5 筆錯誤日誌:\n\n")
                for log in error_logs[-5:]:
                    f.write(f"- `{log['timestamp']}`: {log['message']}\n")
        else:
            f.write("沒有可用的日誌。\n")
