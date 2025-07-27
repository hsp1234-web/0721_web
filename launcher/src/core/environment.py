# launcher/src/core/environment.py

import psutil
import shutil
from pathlib import Path
from rich.console import Console

console = Console()

class EnvironmentManager:
    """負責處理環境相關的檢查與設定。"""

    def __init__(
        self,
        project_path: Path,
        min_disk_space_mb: int = 100,
        max_memory_usage_percent: int = 95,
    ):
        self.project_path = project_path
        self.min_disk_space_mb = min_disk_space_mb
        self.max_memory_usage_percent = max_memory_usage_percent

    def check_disk_space(self) -> bool:
        """檢查剩餘磁碟空間是否充足。"""
        free_space_gb = psutil.disk_usage("/").free / (1024**3)
        console.log(f"可用磁碟空間: {free_space_gb:.2f} GB")
        if free_space_gb * 1024 < self.min_disk_space_mb:
            console.print(
                f"[bold red]錯誤: 磁碟空間不足！至少需要 {self.min_disk_space_mb} MB。[/bold red]"
            )
            return False
        return True

    def check_memory(self) -> bool:
        """檢查記憶體使用率是否在可接受範圍內。"""
        memory_percent = psutil.virtual_memory().percent
        console.log(f"目前記憶體使用率: {memory_percent}%")
        if memory_percent > self.max_memory_usage_percent:
            console.print(
                f"[bold red]錯誤: 記憶體使用率過高！目前為 {memory_percent}%。[/bold red]"
            )
            return False
        return True

    def setup_project_directory(
        self, force_refresh: bool, repo_url: str, branch: str
    ):
        """設定專案目錄，如果不存在則從 Git clone。"""
        if self.project_path.exists() and force_refresh:
            console.log(
                f"偵測到 '強制刷新' 選項，正在刪除舊的專案目錄: {self.project_path}"
            )
            shutil.rmtree(self.project_path)

        if not self.project_path.exists():
            console.log(
                f"專案目錄不存在，正在從 {repo_url} (分支: {branch}) 下載..."
            )
            try:
                # 這裡我們將使用 subprocess 在 installer 模組中呼叫 git
                # 此處僅為邏輯佔位
                pass
            except Exception as e:
                console.print(f"[bold red]下載程式碼失敗: {e}[/bold red]")
                return False
        else:
            console.log(f"專案目錄已存在: {self.project_path}")

        return True

    def run_all_checks(self) -> bool:
        """執行所有環境檢查。"""
        console.log("開始執行環境檢查...")
        if not self.check_disk_space() or not self.check_memory():
            return False
        console.log("[green]環境檢查通過。[/green]")
        return True
