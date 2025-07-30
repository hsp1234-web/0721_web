# -*- coding: utf-8 -*-
"""
核心工具：V3 報告生成器
"""
import sqlite3
from pathlib import Path
import pandas as pd
from datetime import datetime

class ReportGenerator:
    """
    從 logs.sqlite 生成三份標準 Markdown 報告。
    """
    def __init__(self, db_path: Path, report_id: str):
        self.db_path = db_path
        self.report_id = report_id
        self.df = None
        self.start_time = None
        self.end_time = None
        self.total_duration_seconds = 0

    def _load_data(self):
        """從資料庫載入數據到 pandas DataFrame"""
        with sqlite3.connect(self.db_path) as conn:
            self.df = pd.read_sql_query("SELECT * FROM phoenix_logs", conn)

        # 轉換時間戳並設定時區
        self.df['timestamp'] = pd.to_datetime(self.df['timestamp'])
        self.df = self.df.set_index('timestamp')

        self.start_time = self.df.index.min()
        self.end_time = self.df.index.max()
        self.total_duration_seconds = (self.end_time - self.start_time).total_seconds()

    def _format_duration(self, seconds: int) -> str:
        """將秒數格式化為 'X 分 Y 秒'"""
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes} 分 {seconds} 秒"

    def generate_all_reports(self):
        """生成所有報告並返回 Markdown 字串"""
        if self.df is None:
            self._load_data()

        report1 = self._generate_summary_report()
        report2 = self._generate_performance_report()
        report3 = self._generate_log_report()

        return {
            "summary_report.md": report1,
            "performance_report.md": report2,
            "log_report.md": report3,
        }

    def _generate_summary_report(self) -> str:
        """生成綜合任務報告"""
        # 效能摘要
        perf_df = self.df[self.df['level'] == 'PERF'].copy()
        avg_cpu = perf_df['cpu_usage'].mean()
        peak_cpu = perf_df['cpu_usage'].max()
        avg_ram = perf_df['ram_usage'].mean()
        peak_ram = perf_df['ram_usage'].max()

        # 關鍵事件
        key_events = self.df[self.df['level'].isin(['SUCCESS', 'ERROR', 'WARN', 'BATTLE', 'CRITICAL'])].copy()

        # 最終狀態
        status_color = "green" if "ERROR" not in self.df['level'].values and "CRITICAL" not in self.df['level'].values else "red"
        status_text = "執行成功" if status_color == "green" else "執行完畢，但有錯誤發生"

        md = f"""
# 鳳凰之心 - 綜合任務報告

**報告ID:** {self.report_id}
**執行時間:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.end_time.strftime('%Y-%m-%d %H:%M:%S')} (Asia/Taipei)
**總耗時:** {self._format_duration(self.total_duration_seconds)}

---

### 一、 總體結果
**狀態:** <font color="{status_color}">{status_text}</font>

### 二、 效能摘要 (重點)
- **平均 CPU:** {avg_cpu:.1f}%
- **峰值 CPU:** {peak_cpu:.1f}%
- **平均 RAM:** {avg_ram:.1f}%
- **峰值 RAM:** {peak_ram:.1f}%

### 三、 關鍵事件摘要
```
{key_events[['level', 'message']].to_string(index=False, header=False)}
```

### 四、 產出檔案
- {self.report_id}-summary.md
- {self.report_id}-performance.md
- {self.report_id}-logs.md
"""
        return md.strip()

    def _generate_performance_report(self) -> str:
        """生成詳細效能報告"""
        perf_df = self.df[self.df['level'] == 'PERF'].copy()

        summary = {
            'CPU 使用率': (perf_df['cpu_usage'].mean(), perf_df['cpu_usage'].max(), perf_df['cpu_usage'].min()),
            'RAM 使用率': (perf_df['ram_usage'].mean(), perf_df['ram_usage'].max(), perf_df['ram_usage'].min())
        }

        # 時間軸圖表
        resampled = perf_df.resample('5S').mean() # 每 5 秒一個數據點
        timeline = []
        for ts, row in resampled.iterrows():
            cpu_bar = '▓' * int(row['cpu_usage'] / 5)
            ram_bar = '▓' * int(row['ram_usage'] / 5)
            timeline.append(f"{ts.strftime('%H:%M:%S')}  [{cpu_bar.ljust(20)}] {row['cpu_usage']:.1f}%      [{ram_bar.ljust(20)}] {row['ram_usage']:.1f}%")

        md = f"""
# 鳳凰之心 - 詳細效能報告

**報告產生時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Asia/Taipei)
**監控持續時間:** {self._format_duration(self.total_duration_seconds)}

---

### 一、 總體效能摘要

| 指標         | 平均值 | 峰值  | 最低值 |
|--------------|--------|-------|--------|
| CPU 使用率   | {summary['CPU 使用率'][0]:.1f}% | {summary['CPU 使用率'][1]:.1f}% | {summary['CPU 使用率'][2]:.1f}% |
| RAM 使用率   | {summary['RAM 使用率'][0]:.1f}% | {summary['RAM 使用率'][1]:.1f}% | {summary['RAM 使用率'][2]:.1f}% |

### 二、 效能時間軸

**時間      CPU 使用率 (%)                  RAM 使用率 (%)**
```
{chr(10).join(timeline)}
```
"""
        return md.strip()

    def _generate_log_report(self) -> str:
        """生成詳細日誌報告"""
        log_entries = []
        for index, row in self.df.iterrows():
            ts_str = index.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
            log_entries.append(f"[{ts_str} (Asia/Taipei)] [{row['level']}] {row['message']}")

        md = f"""
# 鳳凰之心 - 詳細日誌報告

**報告產生時間:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} (Asia/Taipei)
**任務執行區間:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}

---
```
{chr(10).join(log_entries)}
```
"""
        return md.strip()

if __name__ == '__main__':
    # --- 獨立測試 ---
    print("正在測試 ReportGenerator...")
    # 假設 launch.py 已經執行過，並且 logs/logs.sqlite 已存在
    db_file = Path("logs/logs.sqlite")
    if not db_file.exists():
        print("錯誤：找不到 logs/logs.sqlite。請先執行 launch.py 來生成日誌數據。")
    else:
        report_id = f"PHOENIX-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        generator = ReportGenerator(db_file, report_id)
        reports = generator.generate_all_reports()

        for filename, content in reports.items():
            report_path = Path(f"logs/{report_id}-{filename}")
            report_path.write_text(content, encoding='utf-8')
            print(f"已生成報告: {report_path}")

        print("\n--- Summary Report ---")
        print(reports["summary_report.md"])
        print("\nReportGenerator 測試完畢。")
