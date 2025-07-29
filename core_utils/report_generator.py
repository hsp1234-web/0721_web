# -*- coding: utf-8 -*-
import datetime
import re
from pathlib import Path
import pytz

class ReportGenerator:
    def __init__(self, log_file_path: str, archive_folder: str):
        self.log_file_path = Path(log_file_path)
        self.archive_folder = Path(archive_folder)
        self.lines = []
        self.report_content = ""

    def _read_logs(self):
        """讀取並解析日誌檔案"""
        if not self.log_file_path.exists():
            self.lines = ["[ERROR] Log file not found!"]
            return
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

    def _analyze_performance(self):
        """分析效能指標"""
        self.report_content += "## ⏱️ 效能總結\n\n"
        start_time = None
        end_time = None
        app_times = {}
        current_app = None

        # 正則表達式來匹配時間戳和 App 名稱
        time_regex = re.compile(r'^(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})')
        app_regex = re.compile(r'--- 開始為 App \'(\w+)\' 進行安全安裝 ---')

        for line in self.lines:
            time_match = time_regex.match(line)
            if not time_match:
                continue

            log_time = datetime.datetime.strptime(time_match.group(1), '%Y-%m-%d %H:%M:%S')

            if start_time is None:
                start_time = log_time
            end_time = log_time # 不斷更新，最後一行就是結束時間

            app_match = app_regex.search(line)
            if app_match:
                current_app = app_match.group(1)
                app_times[current_app] = {'start': log_time, 'end': None}

            if current_app and "所有套件均已成功安裝" in line:
                if app_times[current_app]['end'] is None:
                    app_times[current_app]['end'] = log_time

        if start_time and end_time:
            total_duration = (end_time - start_time).total_seconds()
            self.report_content += f"- **總安裝耗時**: `{total_duration:.2f}` 秒\n"

        for app, times in app_times.items():
            if times['start'] and times['end']:
                duration = (times['end'] - times['start']).total_seconds()
                self.report_content += f"- **{app.capitalize()} App 安裝耗時**: `{duration:.2f}` 秒\n"

        self.report_content += "\n"


    def _summarize_errors(self):
        """匯總異常和警告"""
        errors = [line for line in self.lines if '[ERROR]' in line]
        warnings = [line for line in self.lines if '[WARNING]' in line]

        if not errors and not warnings:
            self.report_content += "## ✅ 異常匯總\n\n"
            self.report_content += "太棒了！整個過程沒有任何錯誤或警告。\n\n"
            return

        self.report_content += "## ⚠️ 異常匯總\n\n"
        if warnings:
            self.report_content += "### 警告訊息\n\n"
            self.report_content += "```\n"
            for warning in warnings:
                self.report_content += warning
            self.report_content += "```\n\n"

        if errors:
            self.report_content += "### 錯誤訊息\n\n"
            self.report_content += "```\n"
            for error in errors:
                self.report_content += error
            self.report_content += "```\n\n"


    def generate(self):
        """生成完整的報告"""
        self._read_logs()

        # 設置時區
        tz = pytz.timezone('Asia/Taipei')
        now = datetime.datetime.now(tz)

        self.report_content = f"# 🚀 鳳凰之心 - 執行報告\n\n"
        self.report_content += f"**報告生成時間**: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}\n\n"

        self._analyze_performance()
        self._summarize_errors()

        self.report_content += "---\n*報告由鳳凰之心自動化系統生成*\n"

        return self.report_content

    def save(self):
        """保存報告到檔案"""
        report_str = self.generate()

        if not self.archive_folder.exists():
            self.archive_folder.mkdir(parents=True)

        tz = pytz.timezone('Asia/Taipei')
        now = datetime.datetime.now(tz)
        filename = f"執行報告_{now.strftime('%Y%m%d_%H%M%S')}.md"

        save_path = self.archive_folder / filename
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(report_str)

        print(f"✅ 報告已成功儲存至: {save_path}")
        return save_path

if __name__ == '__main__':
    # 獨立測試
    # 假設我們有一個 launch_logs.txt
    with open("launch_logs.txt", "w") as f:
        f.write("2025-07-29 14:30:00 - [INFO] - --- 開始為 App 'quant' 進行安全安裝 ---\n")
        f.write("2025-07-29 14:30:05 - [INFO] - --- App 'quant' 所有套件均已成功安裝 ---\n")
        f.write("2025-07-29 14:30:06 - [ERROR] - 發生了一個錯誤！\n")

    generator = ReportGenerator(log_file_path="launch_logs.txt", archive_folder="作戰日誌歸檔")
    generator.save()
