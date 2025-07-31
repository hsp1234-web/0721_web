# -*- coding: utf-8 -*-
"""
核心工具：V15 報告生成器
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import pytz

class ReportGenerator:
    """
    從 logs.sqlite 生成三份標準 Markdown 報告。
    """
    def __init__(self, db_path: Path, config_path: Path):
        self.db_path = db_path
        self.config = self._load_config(config_path)
        self.timezone = pytz.timezone(self.config.get("TIMEZONE", "Asia/Taipei"))
        self.df = None
        self.start_time = None
        self.end_time = None
        self.total_duration_seconds = 0
        self.output_dir = Path("logs")
        self.output_dir.mkdir(exist_ok=True)

    def _load_config(self, config_path: Path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_data(self):
        """從資料庫載入數據到 pandas DataFrame"""
        with sqlite3.connect(self.db_path) as conn:
            self.df = pd.read_sql_query("SELECT * FROM phoenix_logs", conn)

        if self.df.empty:
            return

        self.df['timestamp'] = pd.to_datetime(self.df['timestamp']).dt.tz_localize('UTC').dt.tz_convert(self.timezone)
        self.df = self.df.set_index('timestamp')

        self.start_time = self.df.index.min()
        self.end_time = self.df.index.max()
        if pd.notna(self.start_time) and pd.notna(self.end_time):
            self.total_duration_seconds = (self.end_time - self.start_time).total_seconds()
        else:
            self.total_duration_seconds = 0


    def _format_duration(self, seconds: int) -> str:
        """將秒數格式化為 'X 分 Y 秒'"""
        seconds = int(seconds)
        minutes, seconds = divmod(seconds, 60)
        return f"{minutes} 分 {seconds} 秒"

    def generate_all_reports(self):
        """生成所有報告並寫入檔案"""
        self._load_data()

        if self.df is None or self.df.empty:
            print("⚠️ 沒有數據可供生成報告。")
            return

        reports = {
            "summary_report.md": self._generate_summary_report,
            "performance_report.md": self._generate_performance_report,
            "detailed_log_report.md": self._generate_log_report,
        }

        for filename, generator_func in reports.items():
            content = generator_func()
            report_path = self.output_dir / filename
            report_path.write_text(content, encoding='utf-8')
            print(f"✅ 已生成報告: {report_path}")

    def _generate_summary_report(self) -> str:
        """生成綜合戰情簡報"""
        if self.df.empty: return "# 綜合戰情簡報\n\n無數據。"

        # 效能摘要
        perf_df = self.df[self.df['level'] == 'PERF'].copy()
        avg_cpu = perf_df['cpu_usage'].mean() if not perf_df.empty else 0
        peak_cpu = perf_df['cpu_usage'].max() if not perf_df.empty else 0
        avg_ram = perf_df['ram_usage'].mean() if not perf_df.empty else 0
        peak_ram = perf_df['ram_usage'].max() if not perf_df.empty else 0

        # 關鍵事件
        key_events = self.df[self.df['level'].isin(['SUCCESS', 'ERROR', 'WARN', 'BATTLE', 'CRITICAL'])].copy()

        # 最終狀態
        has_errors = "ERROR" in self.df['level'].values or "CRITICAL" in self.df['level'].values
        status_color = "red" if has_errors else "green"
        status_text = "執行完畢，但有錯誤發生" if has_errors else "任務成功"

        md = f"""# 📑 綜合戰情簡報

**報告產生時間:** {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}
**總耗時:** {self._format_duration(self.total_duration_seconds)}

---

### 一、總體結果
**狀態:** <font color="{status_color}">{status_text}</font>

### 二、效能重點
- **平均 CPU 使用率:** {avg_cpu:.1f}%
- **峰值 CPU 使用率:** {peak_cpu:.1f}%
- **平均記憶體使用率:** {avg_ram:.1f}%
- **峰值記憶體使用率:** {peak_ram:.1f}%

### 三、關鍵事件摘要
"""
        if not key_events.empty:
            for _, row in key_events.iterrows():
                md += f"- **[{row['level']}]** {row['message']}\n"
        else:
            md += "- 無關鍵事件記錄。\n"

        return md.strip()

    def _generate_performance_report(self) -> str:
        """生成詳細效能報告"""
        if self.df.empty: return "# 效能分析報告\n\n無數據。"

        perf_df = self.df[self.df['level'] == 'PERF'].copy()
        if perf_df.empty: return "# 效能分析報告\n\n無效能數據。"

        summary = {
            'CPU 使用率': (perf_df['cpu_usage'].mean(), perf_df['cpu_usage'].max(), perf_df['cpu_usage'].min()),
            'RAM 使用率': (perf_df['ram_usage'].mean(), perf_df['ram_usage'].max(), perf_df['ram_usage'].min())
        }

        md = f"""# 📊 效能分析報告

**報告產生時間:** {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}
**監控持續時間:** {self._format_duration(self.total_duration_seconds)}

---

### 一、總體效能摘要

| 指標 | 平均值 | 峰值 | 最低值 |
|---|---|---|---|
| CPU 使用率 | {summary['CPU 使用率'][0]:.1f}% | {summary['CPU 使用率'][1]:.1f}% | {summary['CPU 使用率'][2]:.1f}% |
| 記憶體使用率 | {summary['RAM 使用率'][0]:.1f}% | {summary['RAM 使用率'][1]:.1f}% | {summary['RAM 使用率'][2]:.1f}% |

### 二、詳細數據表
{perf_df[['cpu_usage', 'ram_usage']].to_markdown()}
"""
        return md.strip()

    def _generate_log_report(self) -> str:
        """生成詳細日誌報告"""
        if self.df.empty: return "# 詳細日誌報告\n\n無數據。"

        log_df = self.df[self.df['level'] != 'PERF']
        if log_df.empty: return "# 詳細日誌報告\n\n無日誌數據。"

        md = f"""# 📝 詳細日誌報告

**報告產生時間:** {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}
**任務執行區間:** {self.start_time.strftime('%Y-%m-%d %H:%M:%S')} - {self.end_time.strftime('%Y-%m-%d %H:%M:%S')}

---
```
{log_df[['level', 'message']].to_string()}
```
"""
        return md.strip()
