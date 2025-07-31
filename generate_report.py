# -*- coding: utf-8 -*-
"""
獨立報告生成器 (V16 - 模組化)

這個腳本是一個獨立的工具，專門用來從 SQLite 資料庫生成標準的 Markdown 報告。
它實現了報告產生與主業務邏輯的完全解耦。

使用方法:
    python generate_report.py --db-file /path/to/your/database.db --config-file /path/to/your/config.json
"""
import sqlite3
import pandas as pd
from pathlib import Path
from datetime import datetime
import json
import pytz
import argparse
import sys
import sparklines
import re

class ReportGenerator:
    """
    從指定的 SQLite 資料庫生成三份標準 Markdown 報告。
    """
    def __init__(self, db_path: Path, config_path: Path):
        if not db_path.exists():
            print(f"❌ 錯誤：找不到指定的資料庫檔案: {db_path}")
            sys.exit(1)
        if not config_path.exists():
            print(f"❌ 錯誤：找不到指定的設定檔: {config_path}")
            sys.exit(1)

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
        print("🚀 開始生成報告...")
        self._load_data()

        if self.df is None or self.df.empty:
            print("⚠️ 沒有數據可供生成報告。")
            return

        # 在生成報告前，先進行事件分析
        top_events = self._analyze_events()

        reports = {
            "summary_report.md": lambda: self._generate_summary_report(top_events),
            "performance_report.md": self._generate_performance_report,
            "detailed_log_report.md": self._generate_log_report,
        }

        for filename, generator_func in reports.items():
            content = generator_func()
            report_path = self.output_dir / filename
            report_path.write_text(content, encoding='utf-8')
            print(f"✅ 已生成報告: {report_path}")

        print("🎉 所有報告已成功生成。")

    def _analyze_events(self) -> pd.DataFrame:
        """
        分析日誌中的事件，計算每個主要任務的耗時。
        返回一個包含耗時最長任務的 DataFrame。
        """
        if self.df.empty:
            return pd.DataFrame()

        # 我們只關心 CMD 和 BATTLE 等級的日誌來定義任務邊界
        task_logs = self.df[self.df['level'].isin(['CMD', 'BATTLE', 'SUCCESS', 'ERROR', 'CRITICAL'])].copy()

        events = []
        # 使用正則表達式來捕捉更通用的模式
        start_pattern = r"開始為 (.*) 安裝"
        end_pattern = r"\[(.*)\] 所有依賴已成功安裝"

        # 尋找安裝任務
        for index, log in task_logs.iterrows():
            # 尋找開始事件
            match_start = re.search(start_pattern, log['message'])
            if match_start:
                app_name = match_start.group(1)
                start_time = index

                # 尋找對應的結束事件
                # 這裡我們簡化處理：假設下一個 SUCCESS/ERROR 是對應的結束
                end_log = task_logs[
                    (task_logs.index > start_time) &
                    (task_logs['message'].str.contains(f"[{app_name}] 所有依賴已成功安裝") | task_logs['level'].isin(['ERROR', 'CRITICAL']))
                ].head(1)

                if not end_log.empty:
                    end_time = end_log.index[0]
                    duration = (end_time - start_time).total_seconds()
                    events.append({
                        "任務名稱": f"安裝 {app_name} 的依賴",
                        "耗時 (秒)": duration,
                        "開始時間": start_time,
                        "結束時間": end_time
                    })

        if not events:
            return pd.DataFrame()

        events_df = pd.DataFrame(events)
        return events_df.sort_values(by="耗時 (秒)", ascending=False).head(5)

    def _generate_summary_report(self, top_events: pd.DataFrame) -> str:
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

### 三、耗時最長任務 Top 5
"""
        if not top_events.empty:
            md += top_events.to_markdown(index=False)
        else:
            md += "- 無法分析具體的任務耗時。\n"

        md += "\n\n### 四、關鍵事件摘要\n"

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

        cpu_trend = sparklines.sparklines(perf_df['cpu_usage'].tolist())[0]
        ram_trend = sparklines.sparklines(perf_df['ram_usage'].tolist())[0]

        md = f"""# 📊 效能分析報告

**報告產生時間:** {datetime.now(self.timezone).strftime('%Y-%m-%d %H:%M:%S %Z')}
**監控持續時間:** {self._format_duration(self.total_duration_seconds)}

---

### 一、總體效能摘要

| 指標 | 平均值 | 峰值 | 最低值 | 趨勢 (文字圖) |
|---|---|---|---|---|
| CPU 使用率 | {summary['CPU 使用率'][0]:.1f}% | {summary['CPU 使用率'][1]:.1f}% | {summary['CPU 使用率'][2]:.1f}% | `{cpu_trend}` |
| 記憶體使用率 | {summary['RAM 使用率'][0]:.1f}% | {summary['RAM 使用率'][1]:.1f}% | {summary['RAM 使用率'][2]:.1f}% | `{ram_trend}` |

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

if __name__ == "__main__":
    # 確保腳本執行時，其相依的核心套件都已安裝
    try:
        import pandas
        import pytz
        import tabulate
    except ImportError:
        print("偵測到缺少報告生成所需的核心依賴，請先執行：")
        print("pip install pandas pytz tabulate")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="鳳凰之心 V16 報告生成器")
    parser.add_argument("--db-file", type=Path, required=True, help="來源 SQLite 資料庫的路徑")
    parser.add_argument("--config-file", type=Path, required=True, help="對應的 JSON 設定檔路徑")
    args = parser.parse_args()

    generator = ReportGenerator(db_path=args.db_file, config_path=args.config_file)
    generator.generate_all_reports()
