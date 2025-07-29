# -*- coding: utf-8 -*-
# ╔══════════════════════════════════════════════════════════════════╗
# ║                                                                      ║
# ║      🚀 Colab 資料庫驅動儀表板 v13.0 (Rich 版)                     ║
# ║                                                                      ║
# ╠══════════════════════════════════════════════════════════════════╣
# ║                                                                      ║
# ║   採用 rich 套件，提供美觀、流暢、不閃爍的即時儀表板。             ║
# ║   後端作為守護進程持續運行，前端顯示迴圈永不中斷。                 ║
# ║                                                                      ║
# ╚══════════════════════════════════════════════════════════════════╝

#@title 💎 鳳凰之心 Rich 啟動器 v13.0 { vertical-output: true, display-mode: "form" }
#@markdown ---
#@markdown ### **Part 1: 程式碼與環境設定**
#@markdown > **設定 Git 倉庫、分支或標籤。**
#@markdown ---
#@markdown **後端程式碼倉庫 (REPOSITORY_URL)**
REPOSITORY_URL = "https://github.com/hsp1234-web/0721_web" #@param {type:"string"}
#@markdown **後端版本分支或標籤 (TARGET_BRANCH_OR_TAG)**
TARGET_BRANCH_OR_TAG = "4.2.5" #@param {type:"string"}
#@markdown **專案資料夾名稱 (PROJECT_FOLDER_NAME)**
PROJECT_FOLDER_NAME = "WEB1" #@param {type:"string"}
#@markdown **強制刷新後端程式碼 (FORCE_REPO_REFRESH)**
FORCE_REPO_REFRESH = True #@param {type:"boolean"}
#@markdown ---
#@markdown ### **Part 2: 模式設定**
#@markdown > **用於快速驗證或完整部署。**
#@markdown ---
#@markdown **快速測試模式 (FAST_TEST_MODE)**
#@markdown > 預設開啟。將跳過所有 App 的依賴安裝和啟動，用於快速驗證核心通訊流程。
FAST_TEST_MODE = True #@param {type:"boolean"}

#@markdown ---
#@markdown > **設定完成後，點擊此儲存格左側的「執行」按鈕。**
#@markdown ---

# ==============================================================================
# 🚀 核心邏輯
# ==============================================================================
import os
import sys
import shutil
import subprocess
from pathlib import Path
import time
import sqlite3
import json
from IPython.display import display, HTML, Javascript, clear_output

# 安裝 Rich
try:
    import rich
except ImportError:
    print("安裝 rich 套件...")
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "rich"], check=True)
    print("✅ rich 安裝完成。")

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console()

def make_layout() -> Layout:
    """建立儀表板的版面配置"""
    layout = Layout(name="root")
    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main"),
        Layout(size=5, name="footer"),
    )
    layout["main"].split_row(Layout(name="side"), Layout(name="body", ratio=2))
    layout["side"].split(Layout(name="status_panel"), Layout(name="system_panel"))
    return layout

def get_app_status_table(apps_status: dict) -> Table:
    """建立應用程式狀態表格"""
    table = Table(title="微服務狀態", expand=True)
    table.add_column("Icon", justify="center", style="cyan")
    table.add_column("服務名稱", style="magenta")
    table.add_column("狀態", justify="right", style="green")

    status_map = {"pending": "⚪", "starting": "🟡", "running": "🟢", "failed": "🔴"}
    for app, status in apps_status.items():
        icon = status_map.get(status, "❓")
        table.add_row(icon, app.capitalize(), status)
    return table

def get_log_panel(log_rows: list) -> Panel:
    """建立日誌面板"""
    log_text = ""
    for ts, level, msg in reversed(log_rows):
        ts_str = str(ts).split(" ")[1][:8] if ts else ""
        level_color = {"INFO": "green", "ERROR": "red", "CRITICAL": "bold red"}.get(level, "white")
        log_text += f"[grey50]{ts_str}[/] [{level_color}]{level}[/] [white]{msg}[/]\n"
    return Panel(log_text, title="📜 即時日誌 (最新 10 筆)", border_style="cyan")

base_path = Path("/content")

def main():
    # --- 全域路徑與變數 ---
    project_path = base_path / PROJECT_FOLDER_NAME
    db_file = project_path / "state.db"

    # --- 步驟 1: 準備專案 ---
    console.rule("[bold green]🚀 鳳凰之心 Rich 啟動器 v13.0[/bold green]")
    with console.status("[bold yellow]1. 準備專案目錄...[/]", spinner="earth"):
        if FORCE_REPO_REFRESH and project_path.exists():
            shutil.rmtree(project_path)
        if not project_path.exists():
            git_command = ["git", "clone", "--branch", TARGET_BRANCH_OR_TAG, "--depth", "1", "-q", REPOSITORY_URL, str(project_path)]
            subprocess.run(git_command, check=True, cwd=base_path)
        os.chdir(project_path)
    console.log(f"✅ 專案準備完成於: {os.getcwd()}")

    # --- 步驟 2: 安裝核心依賴 ---
    with console.status("[bold yellow]2. 安裝核心 Python 依賴...[/]", spinner="dots"):
        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "pip"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        all_reqs_path = project_path / "all_requirements.txt"
        with open(all_reqs_path, "w") as outfile:
            for app_dir in (project_path / "apps").iterdir():
                if app_dir.is_dir():
                    req_file = app_dir / "requirements.txt"
                    if req_file.exists():
                        with open(req_file) as infile:
                            outfile.write(infile.read())
                        outfile.write("\n")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", str(all_reqs_path)], check=True)
    console.log("✅ 所有依賴安裝完成。")

    # --- 步驟 3: 在背景啟動後端主力部隊 ---
    console.log("3. 觸發背景服務啟動程序...")
    env = os.environ.copy()
    env["DB_FILE"] = str(db_file)
    if FAST_TEST_MODE:
        env["FAST_TEST_MODE"] = "true"
        console.log("   - 🚀 快速測試模式已啟用。")

    log_file = project_path / "logs" / "launch.log"
    log_file.parent.mkdir(exist_ok=True)

    with open(log_file, "w") as f:
        launch_process = subprocess.Popen(
            [sys.executable, "launch.py"],
            env=env, stdout=f, stderr=subprocess.STDOUT
        )
    console.log(f"✅ 後端主力部隊 (launch.py) 已在背景啟動 (PID: {launch_process.pid})。")
    console.log(f"   - 日誌將寫入: {log_file}")

    # --- 步驟 4: 啟動前端戰情顯示器 ---
    console.log("\n4. 正在啟動前端戰情顯示器...")
    time.sleep(2)

    layout = make_layout()

    with Live(layout, screen=True, redirect_stderr=False, vertical_overflow="visible") as live:
        try:
            while True:
                try:
                    conn = sqlite3.connect(db_file)
                    cursor = conn.cursor()
                    cursor.execute("SELECT current_stage, apps_status, action_url, cpu_usage, ram_usage FROM status_table WHERE id = 1")
                    status_row = cursor.fetchone()
                    cursor.execute("SELECT timestamp, level, message FROM log_table ORDER BY id DESC LIMIT 10")
                    log_rows = cursor.fetchall()
                    conn.close()

                    if not status_row:
                        time.sleep(1)
                        continue
                except sqlite3.OperationalError as e:
                    if "no such table" in str(e):
                        time.sleep(1)
                        continue
                    raise

                stage, apps_status_json, action_url, cpu, ram = status_row
                apps_status = json.loads(apps_status_json) if apps_status_json else {}

                # 更新 Header
                header_text = Text("🚀 鳳凰之心 - 作戰指揮中心 🚀", justify="center", style="bold magenta")
                layout["header"].update(Panel(header_text, border_style="green"))

                # 更新 App 狀態
                layout["status_panel"].update(get_app_status_table(apps_status))

                # 更新系統狀態
                system_table = Table(title="📊 系統資源", expand=True)
                system_table.add_column("項目", style="cyan")
                system_table.add_column("數值", justify="right", style="green")
                system_table.add_row("CPU", f"{cpu or 0.0:.1f}%")
                system_table.add_row("RAM", f"{ram or 0.0:.1f}%")
                layout["system_panel"].update(Panel(system_table, border_style="yellow"))

                # 更新日誌
                layout["body"].update(get_log_panel(log_rows))

                # 更新 Footer (連結和狀態)
                footer_text = f"當前階段: [bold yellow]{stage.upper()}[/]"
                if action_url:
                    footer_text += f"\n\n[bold green]✅ 啟動完成！[/] 點擊連結開啟主儀表板: [link={action_url}]{action_url}[/link]"
                elif stage in ["failed", "critical_failure"]:
                    footer_text += "\n\n[bold red]❌ 啟動失敗。請檢查日誌以了解詳情。[/]"
                layout["footer"].update(Panel(Text(footer_text, justify="center"), border_style="red"))

                live.refresh()
                time.sleep(1)

        except KeyboardInterrupt:
            console.log("\n\n🛑 偵測到手動中斷！正在終止後端服務...")
            launch_process.terminate()
            console.log("✅ 後端服務已被終止。")
        except Exception as e:
            console.print_exception(show_locals=True)

if __name__ == "__main__":
    main()
