# -*- coding: utf-8 -*-
"""
鳳凰之心專案 - 動態記憶體啟動器 (使用 argparse)

此腳本會自動偵測系統環境，並在條件允許的情況下（Linux 且記憶體充足），
將所有微服務的虛擬環境建立在記憶體中，以大幅加速啟動和測試流程。
如果記憶體空間不足，會自動為大型應用降級至磁碟模式。
"""
import asyncio
import os
import platform
import shutil
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List

try:
    import psutil
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("錯誤：缺少必要的套件。請執行 'pip install psutil rich'")
    sys.exit(1)

# --- 全域設定 ---
APP_ROOT_DIR = Path("apps")
VENV_IN_MEMORY_DIR = Path("/dev/shm/phoenix_venvs")
VENV_ON_DISK_DIR = Path(".venvs")
MIN_MEMORY_GB_FOR_RAM_MODE = 1  # 降低閾值以進行測試

# --- rich Console ---
console = Console()


def is_linux() -> bool:
    """檢查作業系統是否為 Linux。"""
    return platform.system() == "Linux"


def has_enough_memory() -> bool:
    """檢查可用記憶體是否大於等於指定閾值。"""
    available_memory_gb = psutil.virtual_memory().available / (1024**3)
    return available_memory_gb >= MIN_MEMORY_GB_FOR_RAM_MODE


def find_phoenix_apps() -> List[Path]:
    """在 'apps' 目錄下尋找所有合法的應用程式。"""
    if not APP_ROOT_DIR.is_dir():
        return []

    valid_apps = []
    for app_dir in APP_ROOT_DIR.iterdir():
        if app_dir.is_dir() and (app_dir / "main.py").exists() and (app_dir / "requirements.txt").exists():
            valid_apps.append(app_dir)
    return valid_apps


async def setup_app_environment(app_path: Path, venv_base_path: Path, allow_fallback: bool = True) -> bool:
    """為單一應用程式建立虛擬環境並安裝依賴。"""
    app_name = app_path.name
    venv_path = venv_base_path / app_name / ".venv"
    requirements_path = app_path / "requirements.txt"
    venv_python = venv_path / "bin" / "python"

    try:
        # 建立虛擬環境
        venv_path.parent.mkdir(exist_ok=True, parents=True)
        proc_venv = await asyncio.create_subprocess_exec(
            "uv", "venv", str(venv_path), "-p", sys.executable,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr_venv = await proc_venv.communicate()

        if proc_venv.returncode != 0:
            console.print(f"[bold red]錯誤：[/bold red] 為應用 '{app_name}' 建立 .venv 失敗。")
            console.print(stderr_venv.decode())
            return False

        # 安裝依賴
        proc_pip = await asyncio.create_subprocess_exec(
            "uv", "pip", "install", "-p", str(venv_python), "-r", str(requirements_path),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        _, stderr_pip_bytes = await proc_pip.communicate()
        stderr_pip = stderr_pip_bytes.decode()

        if proc_pip.returncode != 0:
            # 檢查是否因為記憶體不足而失敗
            if "no space left on device" in stderr_pip.lower() and allow_fallback:
                console.print(f"[bold yellow]警告：[/bold yellow] 應用 '{app_name}' 因記憶體空間不足，自動降級至磁碟模式。")
                # 嘗試在磁碟上重新安裝
                return await setup_app_environment(app_path, VENV_ON_DISK_DIR, allow_fallback=False)

            console.print(f"[bold red]錯誤：[/bold red] 為應用 '{app_name}' 安裝依賴失敗。")
            console.print(stderr_pip)
            return False

        return True
    except Exception as e:
        console.print(f"[bold red]錯誤：[/bold red] 設定應用 '{app_name}' 時發生未預期的例外：{e}")
        return False


def launch_apps(apps: List[Path], ram_apps: List[Path], disk_apps: List[Path]):
    """啟動所有應用程式。"""
    console.print("\n[bold green]🚀 正在啟動所有應用程式...[/bold green]")

    # 啟動記憶體中的應用
    for app_path in ram_apps:
        app_name = app_path.name
        venv_python = VENV_IN_MEMORY_DIR / app_name / ".venv" / "bin" / "python"
        main_py = app_path / "main.py"
        try:
            proc = subprocess.Popen([str(venv_python), str(main_py)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            console.print(f"  - [cyan]{app_name}[/cyan] (記憶體模式) 已啟動 (PID: {proc.pid})")
        except Exception as e:
            console.print(f"[bold red]錯誤：[/bold red] 啟動應用 '{app_name}' 失敗: {e}")

    # 啟動磁碟上的應用
    for app_path in disk_apps:
        app_name = app_path.name
        venv_python = VENV_ON_DISK_DIR / app_name / ".venv" / "bin" / "python"
        main_py = app_path / "main.py"
        try:
            proc = subprocess.Popen([str(venv_python), str(main_py)], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding='utf-8')
            console.print(f"  - [cyan]{app_name}[/cyan] (磁碟模式) 已啟動 (PID: {proc.pid})")
        except Exception as e:
            console.print(f"[bold red]錯誤：[/bold red] 啟動應用 '{app_name}' 失敗: {e}")

    console.print("\n[bold yellow]所有服務皆已在背景執行。[/bold yellow]")


def main():
    parser = argparse.ArgumentParser(description="鳳凰之心專案 - 動態記憶體啟動器")
    parser.add_argument("--force-disk", action="store_true", help="強制使用磁碟來儲存虛擬環境。")
    args = parser.parse_args()

    console.print("[bold cyan]--- 鳳凰之心指揮中心 ---[/bold cyan]")

    apps = find_phoenix_apps()
    if not apps:
        console.print("[bold red]錯誤：[/bold red] 在 'apps' 目錄下找不到任何合法的應用程式。")
        sys.exit(1)

    console.print(f"🔍 發現 {len(apps)} 個應用程式:")
    for app_path in apps:
        console.print(f"  - [green]{app_path.name}[/green]")

    use_ram_mode = is_linux() and has_enough_memory() and not args.force_disk

    if use_ram_mode:
        console.print(f"\n🧠 [bold yellow]記憶體模式已啟用。[/bold yellow] 虛擬環境將優先建立於: {VENV_IN_MEMORY_DIR}")
        if VENV_IN_MEMORY_DIR.exists():
            shutil.rmtree(VENV_IN_MEMORY_DIR)
        VENV_IN_MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    else:
        console.print(f"\n💾 [bold blue]磁碟模式已啟用。[/bold blue] 虛擬環境將建立於: {VENV_ON_DISK_DIR}")

    console.print("\n[bold green]🔧 正在並行設定所有應用程式環境...[/bold green]")

    ram_apps, disk_apps = [], []

    async def run_setup():
        nonlocal ram_apps, disk_apps
        successful_apps = []

        with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:

            async def setup_and_classify(app):
                venv_base_path = VENV_IN_MEMORY_DIR if use_ram_mode else VENV_ON_DISK_DIR
                success = await setup_app_environment(app, venv_base_path)
                if success:
                    # 檢查最終環境在哪裡
                    if (VENV_IN_MEMORY_DIR / app.name / ".venv").exists():
                        ram_apps.append(app)
                    elif (VENV_ON_DISK_DIR / app.name / ".venv").exists():
                        disk_apps.append(app)
                    successful_apps.append(app)
                return success

            tasks = [progress.add_task(f"設定 {app.name}", total=None) for app in apps]
            setup_tasks = [setup_and_classify(app) for app in apps]
            results = await asyncio.gather(*setup_tasks)

        if not all(results):
            console.print("\n[bold red]❌ 部分應用程式環境設定失敗。請檢查上面的錯誤訊息。[/bold red]")
            sys.exit(1)

        console.print("\n[bold green]✅ 所有應用程式環境設定成功！[/bold green]")

    asyncio.run(run_setup())

    launch_apps(apps, ram_apps, disk_apps)


if __name__ == "__main__":
    main()
