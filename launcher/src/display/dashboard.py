# launcher/src/display/dashboard.py

import time
from datetime import datetime
from collections import deque

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
import psutil

console = Console()


from ..core.log_database import LogDatabase

class Dashboard:
    """一個用於顯示專案狀態的 rich 儀表板。"""

    def __init__(self, log_display_lines: int, timezone: str, log_db: LogDatabase = None):
        self.logs = deque(maxlen=log_display_lines)
        self.status = {}
        self.timezone = timezone
        self.log_db = log_db
        self.layout = self._create_layout()
        self._live = Live(self.layout, console=console, screen=True, auto_refresh=False)

    def _create_layout(self) -> Layout:
        """定義儀表板的佈局。"""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=3),
            Layout(ratio=1, name="main"),
            Layout(size=10, name="footer"),
        )
        layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))
        layout["side"].split(Layout(name="status_box"), Layout(name="resource_box"))
        layout["footer"].update(self._generate_log_panel())
        return layout

    def _generate_header(self) -> Panel:
        """產生儀表板的標題。"""
        now = datetime.now()
        header_text = Text(
            f"🚀 鳳凰之心指揮中心 v2.0 | {now.strftime('%Y-%m-%d %H:%M:%S')}",
            justify="center",
        )
        return Panel(header_text, style="bold magenta")

    def _generate_status_panel(self) -> Panel:
        """產生狀態面板。"""
        status_table = Table.grid(expand=True)
        status_table.add_column(justify="left", ratio=1)
        status_table.add_column("status", justify="right", ratio=1)

        for key, value in self.status.items():
            status_table.add_row(f"{key}:", f"[bold green]{value}[/bold green]")

        return Panel(
            status_table, title="[bold cyan]系統狀態[/bold cyan]", border_style="cyan"
        )

    def _generate_resource_panel(self) -> Panel:
        """產生資源監控面板。"""
        resource_table = Table.grid(expand=True)
        resource_table.add_column(justify="left")
        resource_table.add_column("value", justify="right")

        cpu_percent = psutil.cpu_percent()
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        cpu_style = "green" if cpu_percent < 80 else "yellow" if cpu_percent < 95 else "red"
        mem_style = "green" if mem.percent < 80 else "yellow" if mem.percent < 95 else "red"

        resource_table.add_row("CPU 使用率:", f"[{cpu_style}]{cpu_percent:.1f}%[/{cpu_style}]")
        resource_table.add_row("記憶體使用率:", f"[{mem_style}]{mem.percent:.1f}%[/{mem_style}]")
        resource_table.add_row("磁碟空間:", f"{disk.free // (1024**3)} GB 可用")

        return Panel(
            resource_table,
            title="[bold yellow]資源監控[/bold yellow]",
            border_style="yellow",
        )

    def _generate_log_panel(self) -> Panel:
        """產生顯示日誌的面板。"""
        log_text = "\n".join(self.logs)
        return Panel(
            log_text, title="[bold green]作戰日誌[/bold green]", border_style="green"
        )

    def add_log(self, message: str, level: str = "INFO"):
        """新增一條日誌訊息，並可選地寫入資料庫。"""
        now = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{now}] [{level}] {message}"
        self.logs.append(log_entry)

        if self.log_db:
            self.log_db.log(level, message)

        self.update()

    def update_status(self, key: str, value: str):
        """更新狀態面板中的一個鍵值對。"""
        self.status[key] = value
        self.update()

    def update(self):
        """更新整個儀表板的顯示。"""
        self.layout["header"].update(self._generate_header())
        self.layout["status_box"].update(self._generate_status_panel())
        self.layout["resource_box"].update(self._generate_resource_panel())
        self.layout["footer"].update(self._generate_log_panel())
        self._live.refresh()

    def start(self):
        """啟動儀表板的即時更新。"""
        self._live.start()

    def stop(self):
        """停止儀表板的即時更新。"""
        self._live.stop()

if __name__ == '__main__':
    # 測試儀表板
    dashboard = Dashboard(log_display_lines=20, timezone="Asia/Taipei")
    with dashboard._live as live:
        dashboard.add_log("正在初始化...")
        dashboard.update_status("階段", "環境檢查")
        time.sleep(2)

        dashboard.add_log("環境檢查完畢。")
        dashboard.update_status("進度", "50%")
        time.sleep(2)

        dashboard.add_log("正在下載依賴...")
        dashboard.update_status("階段", "安裝依賴")
        time.sleep(2)

        dashboard.add_log("依賴安裝完成。")
        dashboard.update_status("進度", "100%")
        time.sleep(2)
        dashboard.add_log("啟動器測試完成。")
