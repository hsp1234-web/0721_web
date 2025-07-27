# launcher/src/core/installer.py

import subprocess
import sys
from pathlib import Path
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.console import Console
import psutil

console = Console()


class Installer:
    """負責處理程式碼下載和依賴安裝。"""

    def __init__(self, project_path: Path):
        self.project_path = project_path

    def _can_install(
        self, requirements_path: Path, min_disk_space_mb: int = 500
    ) -> bool:
        """
        一個簡化的檢查，確保在安裝大型依賴前仍有足夠空間。
        注意：這是一個粗略的估計。
        """
        # 這裡我們只做一個簡單的磁碟空間檢查
        # 實際的依賴大小估算可能很複雜
        free_space_mb = psutil.disk_usage("/").free / (1024 * 1024)
        if free_space_mb < min_disk_space_mb:
            console.print(
                f"[bold yellow]⚠️  警告: 剩餘磁碟空間 ({free_space_mb:.2f} MB) "
                f"不足 {min_disk_space_mb} MB，[/bold yellow]"
            )
            console.print(
                f"[bold yellow]為避免系統崩潰，將跳過大型依賴 "
                f"'{requirements_path.name}' 的安裝。[/bold yellow]"
            )
            return False
        return True


    def _run_command(self, command: list[str], description: str) -> bool:
        """執行一個子程序命令並顯示進度。"""
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
        ) as progress:
            task = progress.add_task(description, total=None)
            try:
                process = subprocess.Popen(
                    command,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                )
                for line in iter(process.stdout.readline, ""):
                    # 我們可以選擇性地顯示一些輸出，但通常進度條就夠了
                    pass
                process.wait()
                if process.returncode == 0:
                    progress.update(task, completed=100, total=100)  # Mark as complete
                    console.log(f"[green]✅ {description} 完成。[/green]")
                    return True
                else:
                    console.print(
                        f"[bold red]❌ {description} 失敗。返回碼: {process.returncode}[/bold red]"
                    )
                    # 可以在此處印出詳細錯誤
                    # console.print(process.stderr.read())
                    return False
            except Exception as e:
                console.print(f"[bold red]❌ 執行命令時發生錯誤: {e}[/bold red]")
                return False

    def download_code(self, repo_url: str, branch: str):
        """從 Git 下載程式碼。"""
        command = [
            "git", "clone",
            "--branch", branch,
            "--depth", "1",
            repo_url,
            str(self.project_path),
        ]
        return self._run_command(command, f"從 {repo_url} 下載程式碼")

    def install_dependencies(self):
        """安裝 requirements.txt 中的依賴，並在安裝前檢查空間。"""
        requirements_path = self.project_path / "requirements.txt"
        if not requirements_path.exists():
            console.log("⚠️ 找不到 requirements.txt，跳過依賴安裝。")
            return True

        # 在安裝前執行檢查
        if not self._can_install(requirements_path):
            return False # 返回 False 表示未安裝，但這不是一個致命錯誤

        command = [
            sys.executable, "-m", "pip", "install", "-q", "-r", str(requirements_path)
        ]
        return self._run_command(command, "安裝專案依賴")

    def install_core_dependencies(self):
        """安裝啟動器本身需要的核心依賴。"""
        command = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "-q",
            "psutil",
            "pytz",
            "IPython",
            "rich",
            "toml",
        ]
        return self._run_command(command, "安裝啟動器核心依賴")
